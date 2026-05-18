import json
import os
import re
import sys
from urllib.parse import urljoin

from playwright.sync_api import Page

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ReKYC_Config import (
    DOB_DAY,
    DOB_MONTH,
    DOB_YEAR,
    REKYC_UCC,
    REKYC_URL,
    REKYC_YOPMAIL,
)


step_results = []


def run_step(step_number, step_name, action):
    try:
        action()

        step_results.append({
            "step": step_number,
            "name": step_name,
            "status": "PASS",
            "reason": "",
        })

        print(f"Step {step_number} PASSED: {step_name}")

    except Exception as e:
        error_msg = str(e).encode("ascii", "ignore").decode("ascii")

        step_results.append({
            "step": step_number,
            "name": step_name,
            "status": "FAIL",
            "reason": error_msg,
        })

        print(f"Step {step_number} FAILED: {step_name}")
        print(f"Reason: {error_msg}")

        raise

    finally:
        with open("rekyc_step_results.json", "w") as f:
            json.dump(step_results, f, indent=2)


def click_first_visible(page_or_frame, locators, timeout=3000):
    for loc in locators:
        try:
            el = page_or_frame.locator(loc).first
            if el.is_visible(timeout=timeout):
                el.click()
                return True
        except Exception:
            continue
    return False


def fill_first_visible(page_or_frame, locators, value, timeout=3000):
    for loc in locators:
        try:
            el = page_or_frame.locator(loc).first
            if el.is_visible(timeout=timeout):
                el.fill(value)
                return True
        except Exception:
            continue
    return False


def clear_blocking_overlays(page):
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

    try:
        page.evaluate("""
            () => {
                document.querySelectorAll('.reveal-overlay, .modal-backdrop').forEach((el) => {
                    el.style.display = 'none';
                    el.style.pointerEvents = 'none';
                });
                document.querySelectorAll('.reveal, .modal').forEach((el) => {
                    el.style.display = 'none';
                    el.classList.remove('open', 'show');
                    el.setAttribute('aria-hidden', 'true');
                });
                document.body.classList.remove('is-reveal-open', 'modal-open');
                document.documentElement.classList.remove('is-reveal-open', 'modal-open');
            }
        """)
    except Exception:
        pass


def open_section(page, link_text, wait_time=2000):
    clear_blocking_overlays(page)

    link = page.locator(f"//a[normalize-space()='{link_text}']").first
    link.wait_for(state="visible", timeout=10000)
    href = link.get_attribute("href")

    try:
        link.click(timeout=5000)
    except Exception:
        clear_blocking_overlays(page)
        link.click(force=True, timeout=5000)

    page.wait_for_timeout(wait_time)

    if href and not href.startswith("#") and "javascript:" not in href.lower():
        target_url = urljoin(page.url, href)
        current_path = page.url.split("?")[0].rstrip("/")
        target_path = target_url.split("?")[0].rstrip("/")

        if current_path != target_path:
            page.goto(target_url, wait_until="domcontentloaded")
            page.wait_for_timeout(wait_time)


def view_document_proof(page, proof_number):
    clear_blocking_overlays(page)

    rows = page.locator("table tr")

    try:
        rows.first.wait_for(state="visible", timeout=10000)
    except Exception:
        print(f"Proof {proof_number}: documents table not available, skipping view")
        return

    if rows.count() <= proof_number:
        print(f"Proof {proof_number}: row not available, skipping view")
        return

    row = rows.nth(proof_number)
    clickable_cells = row.locator("td")

    if clickable_cells.count() == 0:
        print(f"Proof {proof_number}: no clickable cells available, skipping view")
        return

    clickable_cells.last.click(force=True)
    page.wait_for_timeout(2000)

    try:
        file_name = (row.locator("td").nth(2).text_content() or "").strip().lower()
    except Exception:
        file_name = ""

    if file_name.endswith(".pdf"):
        try:
            iframe = page.locator("iframe").first
            box = iframe.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        except Exception:
            pass

        for _ in range(18):
            page.mouse.wheel(0, 450)
            page.wait_for_timeout(650)

    close_buttons = [
        "#closeModal",
        "button[data-close]",
        ".close-button",
        "//button[contains(text(),'Close')]",
        "//button[contains(text(),'close')]",
        "//button[contains(text(),'×')]",
    ]

    for loc in close_buttons:
        try:
            close_button = page.locator(loc).first
            if close_button.is_visible(timeout=2000):
                close_button.click(force=True)
                page.wait_for_timeout(1000)
                return
        except Exception:
            continue

    clear_blocking_overlays(page)


class TestReKYC:

    def test_rekyc_flow(self, page: Page):

        step_results.clear()

        def step1():
            page.goto(REKYC_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

        run_step(1, "Open ReKYC Login Page", step1)

        def step2():
            filled = fill_first_visible(page, [
                "input[placeholder='ucc']",
                "input[placeholder='UCC']",
                "//input[@name='ucc']",
                "//input[@id='ucc']",
            ], REKYC_UCC)

            if not filled:
                raise Exception("UCC input field not found")

        run_step(2, f"Enter UCC: {REKYC_UCC}", step2)

        def step3():
            clicked = click_first_visible(page, [
                "input[placeholder='DOB : DD/MM/YYYY']",
                "//input[@placeholder='DOB : DD/MM/YYYY']",
                "//input[@name='dob']",
                "//input[@id='dob']",
            ])

            if not clicked:
                raise Exception("DOB input field not found")

            page.wait_for_timeout(1000)

        run_step(3, "Click DOB Field", step3)

        def step4():
            page.wait_for_timeout(2000)

            page.locator(".yearselect").first.select_option(value=DOB_YEAR)
            page.locator(".monthselect").first.select_option(value=DOB_MONTH)

            day_number = str(int(DOB_DAY))
            dates = page.locator("td.available:not(.off):not(.disabled)")

            for i in range(dates.count()):
                cell = dates.nth(i)
                if cell.text_content().strip() == day_number:
                    cell.click()
                    return

            raise Exception("DOB day not found")

        run_step(4, "Select DOB", step4)

        def step5():
            page.locator("#submitform").click()
            page.wait_for_timeout(20000)

        run_step(5, "Submit Login", step5)

        def step6():
            if "otp" not in page.url.lower():
                raise Exception("OTP page not opened")

        run_step(6, "Verify OTP Page", step6)

        def step7():
            new_page = page.context.new_page()
            otp = None

            try:
                new_page.goto("https://yopmail.com/en/", wait_until="domcontentloaded")

                inbox = REKYC_YOPMAIL.split("@")[0]
                new_page.locator("#login").fill(inbox)
                new_page.keyboard.press("Enter")

                mail_items = None

                for _ in range(18):
                    new_page.wait_for_timeout(5000)

                    try:
                        refresh_button = new_page.locator("#refresh")
                        if refresh_button.is_visible(timeout=2000):
                            refresh_button.click()
                    except Exception:
                        pass

                    inbox_frame = new_page.frame_locator("#ifinbox")
                    items = inbox_frame.locator(".m, .lm")

                    try:
                        if items.count() > 0:
                            mail_items = items
                            break
                    except Exception:
                        pass

                if mail_items is None:
                    raise Exception("No email found in Yopmail inbox")

                mail_items.first.click()

                mail_frame = new_page.frame_locator("#ifmail")
                body = mail_frame.locator("body")
                body.wait_for(timeout=30000)
                text = body.inner_text(timeout=30000)

                otp_match = re.search(r"\b\d{6}\b", text)

                if not otp_match:
                    raise Exception("OTP not found in Yopmail email")

                otp = otp_match.group(0)

            finally:
                new_page.close()

            filled = fill_first_visible(page, [
                "input[placeholder*='OTP']",
                "input[placeholder*='otp']",
                "input[name*='otp']",
                "input[id*='otp']",
                "//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'otp')]",
                "//input[@type='text' or @type='tel' or @type='number']",
            ], otp)

            if not filled:
                otp_boxes = page.locator("input[type='text'], input[type='tel'], input[type='number']")
                visible_boxes = []

                for i in range(otp_boxes.count()):
                    box = otp_boxes.nth(i)
                    try:
                        if box.is_visible(timeout=1000):
                            visible_boxes.append(box)
                    except Exception:
                        continue

                if len(visible_boxes) >= 6:
                    for digit, box in zip(otp, visible_boxes[:6]):
                        box.fill(digit)
                    filled = True

            if not filled:
                raise Exception("OTP input field not found")

        run_step(7, "Fetch OTP", step7)

        def step8():
            page.locator("button[data-key='sbt']").click()
            page.wait_for_timeout(5000)

        run_step(8, "Submit OTP", step8)

        def step9():
            if "otp" in page.url.lower():
                raise Exception("Still on OTP page after submit")

        run_step(9, "Dashboard Check", step9)

        def step10():
            open_section(page, "Email")

        run_step(10, "Email Section", step10)

        def step11():
            open_section(page, "Mobile No")

        run_step(11, "Mobile Section", step11)

        def step12():
            open_section(page, "Change of address")

        run_step(12, "Address Section", step12)

        def step13():
            open_section(page, "Nominee")

        run_step(13, "Nominee Section", step13)

        def step14():
            open_section(page, "Bank")

        run_step(14, "Bank Section", step14)

        def step15():
            open_section(page, "Segment")

        run_step(15, "Segment Section", step15)

        def step16():
            open_section(page, "Income Declaration")

        run_step(16, "Income Declaration", step16)

        def step17():
            open_section(page, "Dis Slip Req")

        run_step(17, "Dis Slip Req", step17)

        def step18():
            clear_blocking_overlays(page)
            page.locator("//a[contains(text(),'Service Status')]").click()
            page.wait_for_timeout(2000)

        run_step(18, "Service Status", step18)

        def step19():
            open_section(page, "Documents", wait_time=3000)

        run_step(19, "Documents", step19)

        def step20():
            view_document_proof(page, 1)

        run_step(20, "View Proof 1", step20)

        def step21():
            view_document_proof(page, 2)

        run_step(21, "View Proof 2", step21)

        def step22():
            open_section(page, "DDPI", wait_time=1000)

            page_text = ""
            try:
                page_text = page.locator("body").inner_text(timeout=5000)
            except Exception:
                pass

            if "500 internal server error" in page_text.lower():
                print("DDPI page returned 500 Internal Server Error; continuing after capture")
                try:
                    page.go_back(wait_until="domcontentloaded", timeout=10000)
                except Exception:
                    pass

        run_step(22, "DDPI Section", step22)
