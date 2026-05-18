import ast
import datetime
import html
import json
import os
import smtplib
import subprocess
import sys
import time

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class ReKYC_Agent:

    def run_tests(self):

        print("\n" + "=" * 60)
        print("   RE-KYC AUTOMATION AGENT")
        print("   Fully Automatic - No manual steps needed")
        print("=" * 60)
        print("   Started :", datetime.datetime.now().strftime("%d %b %Y, %I:%M:%S %p"))

        print("\n============================================================")
        print("  STEP 1 | AUTO-LOCATING PROJECT FOLDER")
        print("============================================================")

        project_path = os.getcwd()
        print("  [OK] Project folder found:")
        print("       ", project_path)

        print("\n============================================================")
        print("  STEP 2 | REVIEWING TEST CODE")
        print("============================================================")

        test_file = "tests/ReKYC_Test.py"

        print("  [i] File :", test_file)

        with open(test_file, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            ast.parse(code)
            code_review_status = "PASS"
            print("  [OK] Syntax Check : No errors found")
        except Exception as e:
            code_review_status = "FAIL"
            print("  [ERROR] Syntax Issue :", e)
            self.send_mail("FAIL", code_review_status, [], [], "0s", None)
            return

        tests = [line for line in code.split("\n") if "def test_" in line]
        print("  [OK] Test Functions :", len(tests), "found")

        for test in tests:
            print("       ->", test.strip())

        print("  [OK] Total Lines :", len(code.split("\n")))
        print("\n  [OK] Code Review Complete - Ready to run!")

        print("\n============================================================")
        print("  STEP 3 | RUNNING PYTEST AUTOMATICALLY")
        print("============================================================")

        start_time = time.time()

        print("  [i] Running : pytest tests/")
        print("  [i] LIVE OUTPUT")
        print("-" * 60)

        process = subprocess.Popen(
            [sys.executable, "-m", "pytest", "tests/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        output = ""
        for line in process.stdout:
            print(line, end="")
            output += line

        return_code = process.wait()

        end_time = time.time()
        duration_seconds = int(end_time - start_time)
        duration = f"{duration_seconds // 60}m {duration_seconds % 60}s"

        status = "PASS" if return_code == 0 else "FAIL"

        print("\n  [OK] Execution Completed")
        print("  [OK] Status :", status)
        print("  [OK] Duration :", duration)

        print("\n============================================================")
        print("  STEP 4 | BUILDING STEP RESULTS")
        print("============================================================")

        step_results = self.load_step_results()
        log_lines = output.splitlines()
        video_path = self.find_latest_video()

        print("  [OK] Step Rows :", len(step_results))
        print("  [OK] Video :", video_path if video_path else "Not found")

        print("\n============================================================")
        print("  STEP 5 | SENDING EMAIL REPORT")
        print("============================================================")

        self.send_mail(status, code_review_status, step_results, log_lines, duration, video_path)

    def load_step_results(self):
        if not os.path.exists("rekyc_step_results.json"):
            return []

        try:
            with open("rekyc_step_results.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def find_latest_video(self):
        search_dirs = [
            os.path.join(os.getcwd(), "reports", "videos"),
            os.path.join(os.getcwd(), "test-results"),
            os.path.join(os.getcwd(), "reports"),
        ]

        videos = []

        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue

            for root, _, files in os.walk(search_dir):
                for file_name in files:
                    if file_name.lower().endswith((".webm", ".mp4")):
                        path = os.path.join(root, file_name)
                        videos.append(path)

        if not videos:
            return None

        return max(videos, key=os.path.getmtime)

    def attach_file(self, msg, file_path):
        if not file_path or not os.path.exists(file_path):
            return False

        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(file_path)}",
        )
        msg.attach(part)
        return True

    def send_mail(self, status, code_review_status, step_results, log_lines, duration, video_path):

        print("  [i] EMAIL TRIGGER STARTED")

        sender = "miruthulak21@gmail.com"
        password = "jbor rqbh eniq pkpw"
        receiver = ["miruthulak21@gmail.com", "elamukil@navia.co.in"]

        step_html = ""
        for step in step_results:
            step_status = str(step.get("status", ""))
            icon = "&#9989;" if step_status == "PASS" else "&#10060;"
            color = "#d1fae5" if step_status == "PASS" else "#fee2e2"

            step_html += f"""
            <tr style="background:{color}">
                <td>{html.escape(str(step.get('step', '')))}</td>
                <td>{icon} {html.escape(step_status)}</td>
                <td>{html.escape(str(step.get('name', '')))}</td>
                <td>{html.escape(str(step.get('reason', '')))}</td>
            </tr>
            """

        if not step_html:
            step_html = """
            <tr style="background:#fee2e2">
                <td colspan="4">No step result file found.</td>
            </tr>
            """

        video_line = "Attached to this email" if video_path else "No video file found"
        safe_video_path = html.escape(video_path) if video_path else ""

        email_html = f"""
        <html>
        <body style="font-family:Arial">

            <h2>Re-KYC Automation Report</h2>

            <h3>&#129504; Code Review: {html.escape(code_review_status)}</h3>
            <h3>&#129514; Test Execution: {html.escape(status)}</h3>
            <h3>&#9201; Duration: {html.escape(duration)}</h3>

            <h3>&#128202; Step Results</h3>
            <table border="1" style="border-collapse:collapse;width:100%">
                <tr style="background:#f3f4f6">
                    <th>Step</th>
                    <th>Status</th>
                    <th>Name</th>
                    <th>Reason</th>
                </tr>
                {step_html}
            </table>

            <p><b>Video Recording:</b> {video_line}</p>
            {f"<p><b>Video File:</b> {safe_video_path}</p>" if video_path else ""}

        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = ", ".join(receiver)
        msg["Subject"] = f"Re-KYC Report - {status}"

        msg.attach(MIMEText(email_html, "html"))
        attached = self.attach_file(msg, video_path)

        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender, password)
            server.send_message(msg)
            server.quit()

            print("  [OK] EMAIL SENT SUCCESSFULLY")
            if attached:
                print("  [OK] VIDEO ATTACHED:", video_path)
            else:
                print("  [i] VIDEO NOT FOUND - EMAIL SENT WITHOUT VIDEO")

        except Exception as e:
            print("  [ERROR] EMAIL FAILED:", e)


if __name__ == "__main__":
    agent = ReKYC_Agent()
    agent.run_tests()
