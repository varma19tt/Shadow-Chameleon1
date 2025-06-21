# shadow_chameleon_burp.py
from burp import IBurpExtender
from burp import IContextMenuFactory
from burp import IHttpListener
from java.util import ArrayList
from javax.swing import JMenuItem
import json
import threading
import urllib
import subprocess

class BurpExtender(IBurpExtender, IContextMenuFactory, IHttpListener):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self._callbacks.setExtensionName("Shadow Chameleon")
        
        # Register context menu
        self._callbacks.registerContextMenuFactory(self)
        
        # Register HTTP listener
        self._callbacks.registerHttpListener(self)
        
        print("Shadow Chameleon extension loaded")
    
    def createMenuItems(self, context_menu_invocation):
        self.context = context_menu_invocation
        menu_list = ArrayList()
        
        # Add menu item for selected host
        if context_menu_invocation.getInvocationContext() in [0, 1]:  # Message editor or request/response viewer
            menu_item = JMenuItem("Analyze with Shadow Chameleon", 
                                actionPerformed=self.analyze_target)
            menu_list.add(menu_item)
        
        return menu_list
    
    def analyze_target(self, event):
        # Get selected host
        http_traffic = self.context.getSelectedMessages()
        if not http_traffic:
            return
            
        host = http_traffic[0].getHttpService().getHost()
        
        # Run analysis in background thread
        thread = threading.Thread(
            target=self.run_analysis,
            args=(host,)
        )
        thread.start()
    
    def run_analysis(self, host):
        try:
            # Call our API
            api_url = "http://localhost:8000/analyze"
            data = {
                "target": host,
                "scan_depth": "normal"
            }
            
            # For simplicity, using curl - in production use Python requests
            cmd = [
                "curl",
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(data),
                api_url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                recommendations = json.loads(result.stdout)
                self.show_recommendations(host, recommendations)
            else:
                print(f"Error analyzing {host}: {result.stderr}")
        except Exception as e:
            print(f"Exception analyzing {host}: {str(e)}")
    
    def show_recommendations(self, host, recommendations):
        # Create a tab with recommendations
        tab = self._callbacks.createTextEditor()
        tab.setEditable(False)
        
        content = f"Shadow Chameleon Recommendations for {host}\n\n"
        content += f"Found {len(recommendations)} potential attack vectors\n\n"
        
        for rec in recommendations:
            content += f"=== {rec['name']} ===\n"
            content += f"Confidence: {rec['confidence']*100}%\n"
            content += f"Description: {rec['description']}\n"
            content += "Commands:\n"
            for cmd in rec['commands']:
                content += f"  • {cmd}\n"
            content += "\n"
        
        tab.setText(content)
        
        # Add tab to Burp UI
        self._callbacks.addSuiteTab(f"Shadow Chameleon - {host}", tab.getComponent())
    
    def processHttpMessage(self, tool_flag, message_is_request, message_info):
        # Passive scanning - could be enhanced to automatically analyze traffic
        pass
