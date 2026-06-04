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
from teams_reporter import send_teams_report


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

        sender = "aialerts@navia.co.in"
        username = "emailapikey"
        password = "PHtE6r1eS7jqiG998kUH7afqRZKmN4gtrrw1KQQTt4sTDfJRS01U+d8qlTCwqU0sAPJCRqHKmY1p4rqb4e+Ed26/YW8ZDWqyqK3sx/VYSPOZsbq6x00auVwYdELbVIXqe9di0CzRst3YNA=="
        receiver = ["miruthulak21@gmail.com", "elamukil@navia.co.in", "kiruthika@navia.co.in"]

        step_html = ""
        for step in step_results:
            step_status = str(step.get("status", ""))
            icon = "&#9989;" if step_status == "PASS" else "&#10060;"
            color = "#d1fae5" if step_status == "PASS" else "#fee2e2"

            step_html += f"""
            <tr style="background:{color}">
                <td style="padding:10px;border:1px solid #d1d5db">{html.escape(str(step.get('step', '')))}</td>
                <td style="padding:10px;border:1px solid #d1d5db;font-weight:700">{icon} {html.escape(step_status)}</td>
                <td style="padding:10px;border:1px solid #d1d5db">{html.escape(str(step.get('name', '')))}</td>
                <td style="padding:10px;border:1px solid #d1d5db">{html.escape(str(step.get('reason', '')))}</td>
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
        <body style="margin:0;background:#f4f6f8;font-family:Arial,sans-serif;color:#111827">
            <div style="max-width:1080px;margin:0 auto;padding:20px">
                <div style="background:#ffffff;border:1px solid #e5e7eb">
                    <div style="background:#1f3f68;color:#ffffff;padding:22px 24px">
                        <div style="font-size:22px;font-weight:700">Re-KYC Automation Report</div>
                        <div style="font-size:13px;margin-top:6px">Duration: {html.escape(duration)}</div>
                    </div>
                    <div style="padding:18px 24px 24px">
                        <div style="font-size:14px;font-weight:700;margin-bottom:14px">
                            Code Review: {html.escape(code_review_status)} &nbsp;|&nbsp; Test Execution:
                            <span style="background:{'#dcfce7' if status == 'PASS' else '#fee2e2'};color:{'#047857' if status == 'PASS' else '#b91c1c'};padding:7px 18px;border-radius:5px">{html.escape(status)}</span>
                        </div>
                        <table style="border-collapse:collapse;width:100%;font-size:13px">
                            <thead>
                                <tr style="background:#344153;color:#ffffff;text-align:left">
                                    <th style="padding:10px;border:1px solid #4b5563">Step</th>
                                    <th style="padding:10px;border:1px solid #4b5563">Status</th>
                                    <th style="padding:10px;border:1px solid #4b5563">Name</th>
                                    <th style="padding:10px;border:1px solid #4b5563">Reason</th>
                                </tr>
                            </thead>
                            <tbody>{step_html}</tbody>
                        </table>
                        <div style="font-size:12px;color:#4b5563;margin-top:14px">
                            Video Recording: {video_line}
                            {f"<br>Video File: {safe_video_path}" if video_path else ""}
                        </div>
                    </div>
                </div>
            </div>
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
            server = smtplib.SMTP_SSL("smtp.zatpatmail.com", 465)
            server.login(username, password)
            server.send_message(msg)
            server.quit()

            print("  [OK] EMAIL SENT SUCCESSFULLY")
            if attached:
                print("  [OK] VIDEO ATTACHED:", video_path)
            else:
                print("  [i] VIDEO NOT FOUND - EMAIL SENT WITHOUT VIDEO")
            send_teams_report(
                title=f"Re-KYC Automation Report - {status}",
                status=status,
                html_body=email_html,
                video_path=video_path,
                step_results=step_results,
                duration=duration,
                flow_details={
                    "report_name": "Re-KYC Automation Report",
                    "code_review": code_review_status,
                },
            )

        except Exception as e:
            print("  [ERROR] EMAIL FAILED:", e)


if __name__ == "__main__":
    agent = ReKYC_Agent()
    agent.run_tests()
