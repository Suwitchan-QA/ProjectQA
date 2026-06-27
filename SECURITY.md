# IT Security Policy — ProjectQA

## 1. ข้อมูลที่ห้าม commit ขึ้น GitHub

| ประเภท | ตัวอย่าง |
|--------|----------|
| API Keys / Tokens | Anthropic, Jira, Vansah, Monday, Postman, K6 |
| รหัสผ่าน | AS400, Database, Server |
| Private Keys / Certificates | `.pem`, `.key`, `.p12`, `.jks` |
| ข้อมูล PII | ชื่อ, email, เลขบัตร |
| IP Address ภายใน | Server, AS400 host |
| ผล Test ที่มีข้อมูลจริง | Screenshots, logs, reports |

## 2. การป้องกันที่ติดตั้งไว้ในโปรเจคนี้

### .gitignore
ไฟล์ `.env`, logs, screenshots, certificates ถูก block ไว้ทั้งหมด

### Pre-commit Hook
ทุก commit จะถูกสแกน secret อัตโนมัติ ก่อน push ขึ้น GitHub  
หาก detect พบ → commit จะถูก **block ทันที**

### Security Scanner (manual)
```bash
python scripts/security_scan.py          # สแกนทั้งโปรเจค
python scripts/security_scan.py agent.py # สแกนไฟล์เดียว
```

## 3. วิธีใช้ credentials อย่างปลอดภัย

```bash
# ✅ ถูกต้อง — ใช้ .env
JIRA_API_TOKEN=abc123   # ใน .env (ไม่ขึ้น git)

# ❌ ผิด — hardcode ใน code
jira_token = "abc123"
```

## 4. ถ้า secret หลุดขึ้น GitHub แล้ว

1. **Rotate ทันที** — สร้าง token ใหม่, revoke อันเก่า
2. **ลบออกจาก git history**
   ```bash
   pip install git-filter-repo
   git filter-repo --path-glob '*.env' --invert-paths
   git push --force
   ```
3. แจ้ง IT Security ทันที

## 5. ก่อน share โค้ด / ส่ง PR

- [ ] รัน `python scripts/security_scan.py` ผ่าน 0 findings
- [ ] ตรวจ `.env` ไม่ได้ถูก stage (`git status`)
- [ ] ไม่มี hardcode credentials ใน code
- [ ] Screenshots / logs ไม่มีข้อมูลลูกค้า

## 6. Repository Visibility

Repository นี้ต้อง **Private** เท่านั้น  
ห้าม fork หรือ mirror ออก public โดยไม่ได้รับอนุญาต
