import re
import pdfplumber
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

def clean_text(text):
    text = re.sub(r'(?<!\n)([IVXLCDM]{1,3}\.\s+[^\n]{4,})', r'\n\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def chunk_text(text, max_chars=800):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(clean_text(text))


def describe_table(table_data):
    if not table_data or len(table_data) < 2:
        return ""
    header = [clean_text(cell) if cell else "" for cell in table_data[0]]
    lines = []
    for row in table_data[1:]:
        row = [clean_text(cell) if cell else "" for cell in row]
        subject = row[0] if row else "Nội dung"
        desc = []
        for i in range(1, len(header)):
            col_name = header[i] if i < len(header) else f"Cột {i+1}"
            value = row[i] if i < len(row) else ""
            if value:
                desc.append(f"{col_name.lower()}: {value} tiết")
        lines.append(f"{subject}: {', '.join(desc)}")
    return " ".join(lines)


def extract_pdf_text(pdf_path):
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)


def extract_described_tables(pdf_path):
    described = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for idx, table in enumerate(tables):
                desc = describe_table(table)
                if desc:
                    described.append({
                        "section": f"Bảng {idx+1} trang {page_num}",
                        "subsection": "",
                        "type": "table",
                        "content": desc
                    })
    return described


def process_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])


def extract_sections(text):
    """
    Hệ thống fallback heading thông minh:
    1. Ưu tiên chia theo heading định dạng rõ (Chương, Điều, I. ...).
    2. Nếu không có, chia theo keyword heading thường gặp.
    3. Nếu vẫn không có, fallback chia đoạn đều.
    """
    text = clean_text(text)

    # 1. Heading định dạng phổ biến
    regex_heading = re.compile(r"(?:^|\n)((?:Chương|Điều|Mục|Khoản|[IVXLCDM]{1,4})\.?\s+[^\n]{4,})", re.IGNORECASE)
    matches = list(regex_heading.finditer(text))

    if matches:
        print("[INFO] Heading matched by regex.")
        return split_by_heading_matches(matches, text)

    # 2. Heading keyword thường gặp trong tài liệu Đảng/Nghị quyết
    keyword_headings = [
        "QUAN ĐIỂM CHỈ ĐẠO", "MỤC TIÊU", "NHIỆM VỤ", "GIẢI PHÁP",
        "TỔ CHỨC THỰC HIỆN", "KẾT LUẬN", "PHẦN MỞ ĐẦU"
    ]
    keyword_matches = []
    for heading in keyword_headings:
        pattern = re.compile(rf"\n({heading})", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            keyword_matches.append((match.start(), match.end(), heading))

    if keyword_matches:
        print("[INFO] Heading matched by keyword.")
        keyword_matches.sort()
        sections = []
        for i, (_, end_pos, heading) in enumerate(keyword_matches):
            start = end_pos
            end = keyword_matches[i+1][0] if i+1 < len(keyword_matches) else len(text)
            body = text[start:end].strip()
            for j, chunk in enumerate(chunk_text(body)):
                sections.append({
                    "section": heading.title(),
                    "subsection": f"Đoạn {j+1}",
                    "type": "text",
                    "content": chunk
                })
        return sections

    # 3. Fallback: chia đều toàn văn
    print("[INFO] No heading found. Fallback to uniform chunking.")
    return [{
        "section": "Toàn văn",
        "subsection": f"Đoạn {i+1}",
        "type": "text",
        "content": chunk
    } for i, chunk in enumerate(chunk_text(text))]


def split_by_heading_matches(matches, text):
    sections = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        body = text[start:end].strip()
        for j, chunk in enumerate(chunk_text(body)):
            sections.append({
                "section": title,
                "subsection": f"Đoạn {j+1}",
                "type": "text",
                "content": chunk
            })
    return sections
