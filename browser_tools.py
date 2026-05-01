import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BrowserManager:
    def __init__(self, headless=True):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless

    async def start(self):
        self.playwright = await async_playwright().start()
        # Use Microsoft Edge as requested by the user
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            channel="msedge"
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        )
        self.page = await self.context.new_page()

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url):
        # Increased timeout to 60s and switched to "load" for better reliability on heavy sites
        try:
            await self.page.goto(url, wait_until="load", timeout=60000)
        except Exception as e:
            print(f"Navigation warning (non-fatal): {str(e)}")
            # Even if it timeouts, we still want to try and process what we have

    async def get_page_content(self):
        """Returns the simplified DOM structure for the LLM to process."""
        return await self.page.content()

    async def take_screenshot(self, name="screenshot.png"):
        await self.page.screenshot(path=name)

    async def _safe_evaluate(self, script, retries=3):
        for i in range(retries):
            try:
                return await self.page.evaluate(script)
            except Exception as e:
                if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                    if i < retries - 1:
                        await asyncio.sleep(2) # Wait for navigation/load
                        continue
                raise e

    async def execute_script(self, script, snapshot=None):
        """Executes a generated script with built-in null-safety and error reporting."""
        import json
        
        # Inject the snapshot if provided, so the AI can use 'visible_elements' if it wants
        injection = ""
        if snapshot:
            snapshot_json = json.dumps(snapshot)
            injection = f"window.visible_elements = {snapshot_json};"

        wrapped_script = f"""
        async () => {{
            try {{
                {injection}
                
                // Inject a helper to make interactions safer
                const safeClick = (sel) => {{
                    const el = typeof sel === 'string' ? document.querySelector(sel) : sel;
                    if (!el) return {{ "error": "Element not found for selector: " + sel }};
                    el.click();
                    return {{ "success": true }};
                }};
                
                {script}
                
            }} catch (e) {{
                return {{ "error": e.message }};
            }}
        }}
        """
        try:
            result = await self.page.evaluate(wrapped_script)
            if isinstance(result, dict) and "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_dom_snapshot(self):
        """
        Captures a snapshot of the DOM including visibility and important attributes.
        """
        snapshot_script = """
        () => {
            const elements = document.querySelectorAll('a, button, input, h1, h2, h3, p, span, div[role="button"], textarea, form, section');
            return Array.from(elements).map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    tag: el.tagName.toLowerCase(),
                    text: el.innerText.trim(),
                    id: el.id,
                    name: el.getAttribute('name') || "",
                    title: el.getAttribute('title') || "",
                    role: el.getAttribute('role') || "",
                    classes: el.className || "",
                    label: el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || "",
                    value: el.value || "",
                    isVisible: rect.width > 0 && rect.height > 0,
                    placeholder: el.placeholder || ""
                };
            }).filter(el => el.isVisible && (el.text || el.placeholder || el.name || el.label || el.value || el.title || el.id));
        }
        """
        return await self._safe_evaluate(snapshot_script)

if __name__ == "__main__":
    async def test():
        bm = BrowserManager(headless=False)
        await bm.start()
        await bm.navigate("https://www.google.com")
        snapshot = await bm.get_dom_snapshot()
        print(f"Captured {len(snapshot)} elements")
        await bm.stop()
    
    asyncio.run(test())
