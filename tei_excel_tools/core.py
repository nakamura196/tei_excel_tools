# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['Client']

# %% ../nbs/00_core.ipynb 3
import pandas as pd
from pprint import pprint
from koui.api import KouiAPIClient
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# %% ../nbs/00_core.ipynb 4
class Client:
    def __init__(self, path):
        # self.path = path
        xls = pd.ExcelFile(path)
        self.xls = xls

    def convert(self):
        self.convert_notes()
        self.convert_image()
        self.convert_text()
        self.merge()
        return self.xml_string

    def convert_image(self):
        df = pd.read_excel(self.xls, sheet_name='image')

        pages = {}

        manifest = None

        for index, row in df.iterrows():
            # manifest = row['manifest']

            if manifest is None:
                manifest = row['manifest']

            canvas = row['canvas']
            page_id = row['page_id']
            label = row['label']

            pages[page_id] = {
                # 'manifest': manifest,
                'canvas': canvas,
                "label": label
            }

        self.pages = pages

        root = BeautifulSoup("", "xml")
        
        facsimile = root.new_tag("facsimile")
        facsimile["source"] = manifest

        notes = self.notes

        notesByPages = {}

        for line_id in notes:
            for note in notes[line_id]:
                page_id = note["page_id"]

                if page_id not in notesByPages:
                    notesByPages[page_id] = []

                notesByPages[page_id].append(note)

        for page_id in pages:
            surface = root.new_tag("surface")
            facsimile.append(surface)
            surface["source"] = pages[page_id]["canvas"]
            surface["xml:id"] = page_id

            label = root.new_tag("label")
            surface.append(label)
            label.string = pages[page_id]["label"] or page_id

            '''
            zone = root.new_tag("zone")
            surface.append(zone)
            zone["xml:id"] = page_id
            '''

            if page_id in notesByPages:
                for note in notesByPages[page_id]:
                    zone = root.new_tag("zone")
                    surface.append(zone)
                    zone["xml:id"] = note["note_id"]

                    if "image" in note:
                        xywh = note["image"].split("/")[-4].split(",")
                        
                        x = int(xywh[0])
                        y = int(xywh[1])
                        w = int(xywh[2])
                        h = int(xywh[3])

                        zone["ulx"] = str(x)
                        zone["uly"] = str(y)
                        zone["lrx"] = str(x + w)
                        zone["lry"] = str(y + h)

        self.facsimile = facsimile

    def convert_notes(self):
        df = pd.read_excel(self.xls, sheet_name='notes')

        notes = {}

        for index, row in df.iterrows():
            note_id = row['note_id']
            line_id = row['line_id']
            pos = row['pos']
            type = row['type']
            subtype = row['subtype']
            image = row['image']
            text = row['text']
            page_id = row["page_id"]

            if line_id not in notes:
                notes[line_id] = []

            # if pos not in notes[line_id]:
            #     notes[line_id][pos] = []

            note = {
                "pos": int(pos) if not pd.isnull(pos) else None,
                'note_id': note_id,
                'type': type,
                'subtype': subtype,
                # 'image': image,
                'text': text,
                "page_id": page_id
            }

            if not pd.isnull(image):
                note["image"] = image

            notes[line_id].append(note)

        self.notes = notes

    def convert_text(self):
        df = pd.read_excel(self.xls, sheet_name='text')

        lines = {}

        page_ids = []

        abs = None
        div = []

        for index, row in df.iterrows():
            page_id = row['page_id']
            line_id = row['line_id']
            text1 = row['text1']
            text2 = row["text2"]

            # 新しいページ
            if page_id not in page_ids:
                page_ids.append(page_id)

                if abs is not None:
                    div.append("<ab>"+ "\n".join(abs) + "</ab>")

                abs = []

                # pbの追加
                div.append(Client.createPb(page_id))

            # 当該行に対応するノートを取得
            notes_ = []

            notes = self.notes
            
            if line_id in notes:
                notes_ = notes[line_id]

            # 眉のノートを追加
            abs = Client.add_notes(abs, notes_, "眉")

            ####################

            # lbの追加
            lb = f'<lb xml:id="{line_id}"/>'
            abs.append(lb)

            ####################

            if pd.isnull(text1):
                continue
            
            text1 = Client.replace_kigo_around_x(text1)

            text1 = Client.add_asta(text1, notes_)

            text2 = Client.replace_kigo_around_x(text2)

            soup = KouiAPIClient.convert("text1", text1, "text2", text2, "xml")

            line = Client.get_line(text1, text2, notes_)

            abs.append(line)

            #####

            ### あし
            abs = Client.add_notes(abs, notes_, "脚")

        # 最後
        div.append("<ab>"+ "\n".join(abs) + "</ab>")

        # div_string = "<div>" + "\n".join(div) + "</div>"
        div_string = "\n".join(div)

        self.div_string = div_string

    @staticmethod
    def get_line(text1, text2, notes_):
        soup = KouiAPIClient.convert("a", text1, "b", text2, "xml")

        line = soup.find_all("p")[1]

        apps = line.find_all("app")

        for i in range(len(apps)):

            app = apps[len(apps) - i - 1]

            lem = app.find("lem")
            rdg = app.find("rdg")

            lem_text = lem.text
            rdg_text = rdg.text

            lem_type = None
            rdg_type = None

            lem_certain = None
            rdg_certain = None

            if "(" in lem_text:
                lem_type = "damage"
                
                if "((" in lem_text:
                    lem_certain = "low"

            if "<" in lem_text:
                lem_type = "error"

                if "<<" in lem_text:
                    lem_certain = "low"

            if "(" in rdg_text:
                rdg_type = "damage"
                
                if "((" in rdg_text:
                    rdg_certain = "low"

            if "<" in rdg_text:
                rdg_type = "error"

                if "<<" in rdg_text:
                    rdg_certain = "low"

            lem_text = lem_text.replace("(", "").replace(")", "").replace("<", "").replace(">", "")
            rdg_text = rdg_text.replace("(", "").replace(")", "").replace("<", "").replace(">", "")

            '''
            if "*" in lem.text: 
                c = lem.text.count("*")
                app.insert_after("*" * c)
                app.decompose()
            elif lem.text != rdg.text:
            '''
            if lem_text != rdg_text:
                choice = soup.new_tag("choice")
                app.insert_after(choice)

                orig = soup.new_tag("orig")

                if lem_type:
                    orig["type"] = lem_type

                if lem_certain:
                    orig["certainty"] = lem_certain

                choice.append(orig)
                orig.append(lem_text)

                reg = soup.new_tag("reg")

                if rdg_type:
                    reg["type"] = rdg_type

                if rdg_certain:
                    reg["certainty"] = rdg_certain

                choice.append(reg)
                reg.append(rdg_text)
            app.decompose()

        line = str(line).replace("<p>", "").replace("</p>", "")

        line = Client.replace_asta(line, notes_)

        line = Client.convert_x2space(line)

        line = "<seg>"  + line + "</seg>"

        return line

    def merge(self):
        tei_string = f"""<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
        <teiHeader>
  <fileDesc>
   <titleStmt>
    <title></title>
   </titleStmt>
   <publicationStmt><ab></ab></publicationStmt>
   <sourceDesc>
    <ab></ab>
   </sourceDesc>
  </fileDesc></teiHeader>
        <text>
        <body>
        {self.div_string}
        </body>
        </text>
        </TEI>
        """
        tei_e = BeautifulSoup(tei_string, "xml")

        tei_e.find("TEI").append(self.facsimile)

        self.xml_string = tei_e.prettify()
 
    @staticmethod
    def convertExcel(path):
        ins = Client(path)
        return ins.convert()

    @staticmethod
    def save(xml_string, path):
        f = open(path, 'w')
        f.write(xml_string)
        f.close()

    @staticmethod
    def replace_kigo_around_x(text):
        for n in range(10):
            target = "<" + "X" * n + ">"
            # text = text.replace(target, f"<space quantity='{n}'/>")
            text = text.replace(target, "X" * n)
        return text.strip()

    @staticmethod
    def add_notes(abs, notes_, type):
        for note in notes_:
            if note["pos"] is None:

                if note["subtype"] == type:

                    note = f'<note corresp="#{note["note_id"]}" type="{note["type"]}" subtype="{note["subtype"]}">{note["text"]}</note>'
                    abs.append(note)

        return abs

    @staticmethod
    def convert_x2space(text):
        for n in range(0, 10):
            index = 10 - n
            target = "X" * index
            text = text.replace(target, f"<space quantity=\"{index}\"/>")

        return text

    @staticmethod
    def replace_from_last(text, target_str, replace_str):
        line = text
        line = line[::-1]
        line = line.replace(target_str, replace_str[::-1], 1)
        line = line[::-1]
        return line

    @staticmethod
    def createPb(page):
        # page_num = int(page.split("-")[1])
        return f"<pb corresp=\"#{page}\"/>"

    @staticmethod
    def add_asta(text, notes_):
        for i in range(len(notes_)):
            note = notes_[len(notes_) - i - 1]

            if note["pos"] is not None:

                pos = note["pos"]

                text = text[:note["pos"]] + "*" + text[note["pos"]:]

        return text

    @staticmethod
    def replace_asta(text, notes_):

        for i in range(len(notes_)):
            note = notes_[len(notes_) - i - 1]

            if note["pos"] is not None:
                subtype_string = f' subtype="{note["subtype"]}"' if not pd.isnull(note["subtype"]) else ""
                note_string = f'<note corresp="#{note["note_id"]}" type="{note["type"]}"{subtype_string}>{note["text"]}</note>'            
                text = Client.replace_from_last(text, "*", note_string)

        return text
