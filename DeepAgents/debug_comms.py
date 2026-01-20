from agent_brain import AgentComms

print("🔍 Inspecting Agent Messages Table...")

comms = AgentComms(password="d1204l0723")
if not comms.connect():
    print("❌ Failed to connect to DB")
    exit(1)

sql = "SELECT id, sender, recipient, status, left(content, 50) as snippet, timestamp FROM agent_messages ORDER BY id DESC LIMIT 10"

with comms.conn.cursor() as cur:
    cur.execute(sql)
    rows = cur.fetchall()

if not rows:
    print("📭 Table is empty.")
else:
    print(f"found {len(rows)} messages:")
    for r in rows:
        print(f"ID: {r[0]} | From: {r[1]} -> To: {r[2]} | Status: {r[3]} | Content: {r[4]}... | Time: {r[5]}")

print("\nChecking specifically for unread messages for 'Cinematographer':")
unread_sql = "SELECT count(*) FROM agent_messages WHERE recipient = 'Cinematographer' AND status = 'unread'"
with comms.conn.cursor() as cur:
    cur.execute(unread_sql)
    count = cur.fetchone()[0]
    print(f"Unread Count for 'Cinematographer': {count}")
