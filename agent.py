import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from browser_tools import BrowserManager

# Load environment variables from the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
load_dotenv(os.path.join(project_root, ".env"))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use Gemini Flash Latest - Verified to have valid quotas on this account
MODEL_NAME = "gemini-flash-lite-latest" 

class ScrapingAgent:
    def __init__(self, goal, url, on_step=None):
        self.goal = goal
        self.url = url
        self.browser = BrowserManager(headless=False) # Headless=False for debugging
        self.history = []
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.on_step = on_step
        self.log_file = open("agent_run.log", "a") # Append mode

    def log(self, msg):
        print(msg)
        self.log_file.write(msg + "\n")
        self.log_file.flush()

    async def run(self):
        self.log(f"--- Starting Agent for Goal: {self.goal} ---")
        await self.browser.start()
        await self.browser.navigate(self.url)
        
        retry_count = 0
        max_retries = 3
        success = False
        final_result = None

        try:
            while retry_count < max_retries and not success:
                # 1. Capture Page State
                snapshot = await self.browser.get_dom_snapshot()
                
                # 2. Ask Gemini for next action
                try:
                    action_plan = await self.get_action_from_gemini(snapshot)
                    self.log(f"Agent Plan: {action_plan.get('thought')}")
                except Exception as e:
                    self.log(f"Gemini Error: {str(e)}")
                    break
                
                # 3. Handle Completion or Execute script
                script = action_plan.get("python_code")
                
                if action_plan.get("status") == "DONE":
                    self.log("Goal reached!")
                    success = True
                    
                    if self.on_step:
                        await self.on_step({
                            "thought": action_plan.get("thought"),
                            "code": None,
                            "success": True,
                            "result": action_plan.get("answer") or "Goal reached",
                            "error": None
                        })
                        
                    # If the AI provided an 'answer', use it. Otherwise, try to execute one last script if provided.
                    if action_plan.get("answer"):
                        final_result = action_plan.get("answer")
                        break
                    elif script:
                        self.log(f"Executing final proposed code...")
                        result = await self.browser.execute_script(script, snapshot=snapshot)
                        final_result = result.get("result")
                        break
                    else:
                        self.log("Agent finished without providing a final result.")
                        break

                if not script:
                    self.log("No code generated. Stopping.")
                    break

                self.log(f"Executing proposed code...")
                result = await self.browser.execute_script(script, snapshot=snapshot)
                
                if self.on_step:
                    await self.on_step({
                        "thought": action_plan.get("thought"),
                        "code": script,
                        "success": result["success"],
                        "result": result.get("result"),
                        "error": result.get("error")
                    })

                if not result["success"]:
                    self.history.append({
                        "action": script,
                        "error": result["error"]
                    })
                    retry_count += 1
                    self.log(f"Retrying... ({retry_count}/{max_retries})")
        finally:
            await self.browser.stop()
            # self.log_file.close() # Keep open for next runs if using same instance, or close in a separate method
        
        if not success:
            raise Exception("Agent stopped before reaching the goal. Check agent_run.log for details.")
        
        return final_result

    async def get_action_from_gemini(self, snapshot):
        prompt = f"""
        You are an expert web scraping agent. 
        Your goal is: {self.goal}
        The current URL is: {self.url}
        
        Visible elements:
        {snapshot}

        Execution History (Errors):
        {self.history}

        Analyze the elements and generate the next step. 
        
        CRITICAL RULES:
        1. 'python_code' MUST be valid Javascript that runs in the browser.
        2. Do NOT use variables like 'snapshot' or 'visible_elements' in your Javascript. They do not exist in the browser scope.
        3. Use standard 'document.querySelector' or 'document.querySelectorAll' to find elements.
        4. If a standard element (like a search bar) isn't in 'Visible elements', try a common selector like 'input[name="q"]' or 'textarea[name="q"]' anyway.
        5. If you have already found the answer in the provided 'Visible elements', set status to 'DONE' and provide the 'answer'.
        
        Return ONLY a JSON object with this format:
        {{
            "thought": "brief reasoning about what to do next",
            "python_code": "Javascript to execute. Example: document.querySelector('.price').innerText",
            "status": "CONTINUE or DONE",
            "answer": "If status is DONE, provide the final extracted data here."
        }}
        """
        # Retry logic for Gemini API (429 handling)
        max_api_retries = 3
        for attempt in range(max_api_retries):
            try:
                response = await self.model.generate_content_async(prompt)
                text = response.text.strip()
                break
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    if attempt < max_api_retries - 1:
                        # Increase wait time for free tier
                        wait_time = (attempt + 1) * 30
                        self.log(f"Gemini Rate Limit hit. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                raise e

        # Robust JSON cleaning for AI responses
        import json
        
        # 1. Look for the outermost { and }
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start != -1 and end != -1:
            json_str = text[start:end]
            
            # 2. Scrub markdown indicators or common unformatted text issues
            # Remove any leading/trailing backticks or "json"/ "JSON" prefixes
            clean_json = json_str.strip('`').strip()
            if clean_json.lower().startswith('json'):
                clean_json = clean_json[4:].strip()
                
            try:
                return json.loads(clean_json)
            except json.JSONDecodeError as jde:
                self.log(f"JSON Parse Warning: {str(jde)}. Raw text found between curly braces: {clean_json}")
                raise ValueError(f"AI returned malformed JSON: {clean_json}")
        else:
            self.log(f"No JSON block found in AI response: {text}")
            raise ValueError(f"No JSON found in response")

if __name__ == "__main__":
    async def main():
        agent = ScrapingAgent(
            goal="Search for 'Python' on Google and extract the title of the first search result.",
            url="https://www.google.com"
        )
        result = await agent.run()
        print(f"Final Result: {result}")

    # Use a more robust asyncio run for Windows
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
