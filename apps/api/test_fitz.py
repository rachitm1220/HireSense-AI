import pymupdf

def test():
    try:
        doc = pymupdf.open("/home/vallabh2909/Projects/HireSenseAI/resume.pdf")
        for page in doc:
            links = page.get_links()
            for link in links:
                if link.get("kind") == pymupdf.LINK_URI:
                    rect = link.get("from")
                    text = page.get_textbox(rect).strip()
                    uri = link.get("uri")
                    print(f"[{text}]({uri})")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
