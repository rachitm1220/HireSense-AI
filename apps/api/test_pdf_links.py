import pypdf

def extract_links(pdf_path):
    print(f"Reading: {pdf_path}")
    pdf_reader = pypdf.PdfReader(pdf_path)
    links = set()
    for i, page in enumerate(pdf_reader.pages):
        print(f"Page {i+1}:")
        if "/Annots" in page:
            try:
                annots = page["/Annots"]
                if hasattr(annots, "get_object"):
                    annots = annots.get_object()
                
                print("  Annots found. Type:", type(annots))
                if isinstance(annots, list):
                    for annot in annots:
                        try:
                            annot_obj = annot.get_object() if hasattr(annot, "get_object") else annot
                            if "/A" in annot_obj and "/URI" in annot_obj["/A"]:
                                uri = str(annot_obj["/A"]["/URI"])
                                print(f"    Found URI: {uri}")
                                links.add(uri)
                            else:
                                print(f"    Annot missing URI. Keys: {annot_obj.keys()}")
                        except Exception as e:
                            print(f"    Error on annot: {e}")
            except Exception as e:
                print("  Error processing /Annots:", e)
        else:
            print("  No /Annots on this page.")
            
    print("\nTotal Links Extracted:")
    for link in links:
        print(link)

if __name__ == "__main__":
    extract_links("../../resume.pdf")
