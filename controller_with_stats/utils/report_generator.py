from io import BytesIO
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether

class ReportGenerator:
    PRIMARY=colors.HexColor("#16325C")
    ACCENT=colors.HexColor("#DCEAF7")
    LIGHT=colors.HexColor("#F7FAFC")
    GRID=colors.HexColor("#AAB7C4")

    @classmethod
    def _page(cls,canvas,doc):
        width,height=landscape(A4)
        canvas.saveState()
        canvas.setStrokeColor(cls.PRIMARY)
        canvas.setLineWidth(2)
        canvas.rect(0.55*cm,0.55*cm,width-1.1*cm,height-1.1*cm)
        canvas.setStrokeColor(colors.HexColor("#7FA4C5"))
        canvas.setLineWidth(0.7)
        canvas.rect(0.75*cm,0.75*cm,width-1.5*cm,height-1.5*cm)
        canvas.setFont("Helvetica",8)
        canvas.setFillColor(colors.HexColor("#5B6770"))
        canvas.drawRightString(width-1.0*cm,0.82*cm,f"Page {doc.page}")
        canvas.restoreState()

    @classmethod
    def _styles(cls):
        base=getSampleStyleSheet()
        return {
            "title":ParagraphStyle("StatsTitle",parent=base["Title"],fontName="Helvetica-Bold",fontSize=20,leading=24,textColor=cls.PRIMARY,alignment=TA_CENTER,spaceAfter=12),
            "subtitle":ParagraphStyle("StatsSubtitle",parent=base["BodyText"],fontSize=9,leading=13,textColor=colors.HexColor("#4A5568"),alignment=TA_CENTER,spaceAfter=12),
            "heading":ParagraphStyle("StatsHeading",parent=base["Heading2"],fontName="Helvetica-Bold",fontSize=12,leading=15,textColor=cls.PRIMARY,spaceBefore=8,spaceAfter=7),
            "body":ParagraphStyle("StatsBody",parent=base["BodyText"],fontSize=8,leading=10,alignment=TA_LEFT)
        }

    @classmethod
    def _value(cls,value,style):
        if value is None: value=""
        if isinstance(value,float): value=round(value,3)
        return Paragraph(escape(str(value)),style)

    @classmethod
    def _table(cls,dataframe,style):
        if dataframe is None or dataframe.empty: return Paragraph("No records available.",style)
        frame=dataframe.copy().fillna("")
        headers=[Paragraph(f"<b>{escape(str(column))}</b>",style) for column in frame.columns]
        data=[headers]+[[cls._value(value,style) for value in row] for row in frame.astype(object).values.tolist()]
        usable=landscape(A4)[0]-2.2*cm
        weights=[]
        for column in frame.columns:
            sample=[str(column)]+[str(x) for x in frame[column].head(25).tolist()]
            weights.append(max(7,min(24,max(len(x) for x in sample))))
        total=sum(weights) or 1
        widths=[usable*(weight/total) for weight in weights]
        table=Table(data,colWidths=widths,repeatRows=1,hAlign="CENTER")
        commands=[("BACKGROUND",(0,0),(-1,0),cls.PRIMARY),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.35,cls.GRID),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]
        for row in range(1,len(data)):
            if row%2==0: commands.append(("BACKGROUND",(0,row),(-1,row),cls.LIGHT))
        table.setStyle(TableStyle(commands))
        return table

    @classmethod
    def _metrics(cls,metrics,style):
        if not metrics: return []
        items=[]
        pairs=list(metrics.items())
        for start in range(0,len(pairs),4):
            chunk=pairs[start:start+4]
            data=[[Paragraph(f"<b>{escape(str(k))}</b>",style) for k,_ in chunk],[Paragraph(escape(str(v)),style) for _,v in chunk]]
            table=Table(data,colWidths=[6.1*cm]*len(chunk),hAlign="CENTER")
            table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),cls.ACCENT),("GRID",(0,0),(-1,-1),0.5,cls.GRID),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
            items.extend([table,Spacer(1,8)])
        return items

    @classmethod
    def build(cls,title,details=None,metrics=None,sections=None):
        buffer=BytesIO()
        doc=SimpleDocTemplate(buffer,pagesize=landscape(A4),leftMargin=1.1*cm,rightMargin=1.1*cm,topMargin=1.1*cm,bottomMargin=1.2*cm,title=title)
        styles=cls._styles()
        story=[Paragraph(escape(title),styles["title"])]
        if details:
            detail_text=" &nbsp; | &nbsp; ".join(f"<b>{escape(str(k))}:</b> {escape(str(v))}" for k,v in details.items())
            story.append(Paragraph(detail_text,styles["subtitle"]))
        story.extend(cls._metrics(metrics,styles["body"]))
        for index,(heading,dataframe) in enumerate(sections or []):
            if index: story.append(Spacer(1,8))
            story.append(Paragraph(escape(str(heading)),styles["heading"]))
            story.append(cls._table(dataframe,styles["body"]))
        doc.build(story,onFirstPage=cls._page,onLaterPages=cls._page)
        buffer.seek(0)
        return buffer.getvalue()
