// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
const MarkdownIt = require('markdown-it');
// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed

const DETECTION_API = "https://[Detector_Domain]:6006/analyze?debug=1";
// const OLLAMA_API_URL = 'http://localhost:11434/api/generate';
const ANALYSIS_API = "https://[Analyser_Domain]:8008/fix";
// const MODEL_NAME = 'qwen-docker';  // 使用本地模型，例如 `mistral`
const md = new MarkdownIt({ breaks: false });
let webviewPanel: vscode.WebviewPanel | undefined = undefined;

interface RiskItem {
    risk_type: string;
    snippet: string;
    start: number;
    end: number;
}

interface AnalyzeResult {
    predicted_risks: RiskItem[];
}

export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "dockersec" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	const disposable = vscode.commands.registerCommand('dockersec.checkDockerfileSecurity',async (uri?: vscode.Uri) => {
		
		let dockerfileContent = "";
		if (uri) {
			console.log('uri: ' + uri);
            // 右键 Dockerfile 文件
            const fileContent = await vscode.workspace.fs.readFile(uri);
            dockerfileContent = Buffer.from(fileContent).toString('utf8');
		} else {
			
            // 右键选中 Dockerfile 代码
            const editor = vscode.window.activeTextEditor;
			console.log('editor: ' + editor);
            if (editor) {
                dockerfileContent = editor.document.getText(editor.selection);
            }
        }
		if (!dockerfileContent) {
            vscode.window.showWarningMessage("Dockerfile code or file not selected!");
            return;
        }
		console.log(dockerfileContent);
		vscode.window.showInformationMessage(dockerfileContent);


		// 调用 LLM 进行分析
        vscode.window.showInformationMessage("Analyzing Dockerfile security...");
        
		const risks: AnalyzeResult = await detectDockerfileWithLLM(dockerfileContent);
		
		console.log(risks);
		remediateWithLLM(dockerfileContent, risks);

	});
	
	// vscode.window.showInformationMessage('async finish');
	context.subscriptions.push(disposable);
}

async function detectDockerfileWithLLM(dockerfile: string) {

	try {

		const response = await fetch(DETECTION_API, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				dockerfile_content: dockerfile,
			})
		});

		if (!response.ok) {
            throw new Error(`Error happend in detection API: ${response.statusText}`);
        }
		const result = await response.json();
		return result as AnalyzeResult;

	}catch(error){
		vscode.window.showErrorMessage("The detection interface timed out, and the request failed:" + (error as Error).message);
		throw new Error('Error happend in detection API!');
	}

}


// function formatRiskAnalysis(result: AnalyzeResult): string {
//     if (!result.predicted_risks || result.predicted_risks.length === 0) {
//         return "There is not any risk in the file.";
//     }

//     const lines = result.predicted_risks.map((risk, index) => {
//         const position = (risk.start !== -1 && risk.end !== -1)
//             ? `character ${risk.start}-${risk.end}`
//             : "without position";
        
//         return `- Risk type: ${risk.risk_type}, Snappint: ${risk.snippet}, Position: ${position}`;
//     });

//     return lines.join('\n');
// }

async function remediateWithLLM(dockerfile: string, risks: AnalyzeResult) {
    try {

		console.log(JSON.stringify({
			dockerfile: dockerfile,
			predicted_risks: risks.predicted_risks
		}, null, 2));

		//修改后代码
		const response = await fetch(ANALYSIS_API, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				dockerfile: dockerfile,
				predicted_risks: risks.predicted_risks
			})
		});


		// 获取响应体作为流
		if (!response.body) {
			throw new Error('No response body found');
		}
		const reader = response.body.getReader();

		const decoder = new TextDecoder(); // 用于将字节流转换为字符串
		let done = false;
		let result = "";
		let buffer = ""; // 缓存未解析的 JSON 数据

		while (!done) {
			const { value, done: readerDone } = await reader.read() || { value: new Uint8Array(), done: false };
			done = readerDone;
			buffer += decoder.decode(value, { stream: true });
			let parts = buffer.split("\n");
			buffer = parts.pop() || "";
			for (let part of parts) {
				try {
					const json = JSON.parse(part.trim()); // 解析每一部分的 JSON 数据
					console.log(JSON.stringify(json));
					result += json.response;
					showAnalysisResult(result);
					if (json.done) {
						vscode.window.showInformationMessage("Dockerfile security analysis is completed!");
						return;
					}
				} catch (error) {
					console.error("Analysis failed!", error);
				}	
			}
		}
		

	} catch (error) {
		vscode.window.showErrorMessage("The analysis interface timed out and the request failed:" + (error as Error).message);
	}
}


// 创建 Webview 面板
function createWebviewPanel() {

    if (!webviewPanel) {
        webviewPanel = vscode.window.createWebviewPanel(
            'dockerfileSecurityAnalysis', // panel ID
            'Dockerfile Security Analysis', // 面板标题
            vscode.ViewColumn.Beside, // 在侧边栏显示
            { enableScripts: true } // 启用脚本
        );

		// 监听用户关闭 Webview
        webviewPanel.onDidDispose(() => {
            webviewPanel = undefined; // 清空引用，下次触发重新创建
        });
    }

    return webviewPanel;
}




// 更新 Webview 面板内容
function showAnalysisResult(response: string) {
    const panel = createWebviewPanel(); // 获取现有面板，若不存在则创建一个

	const htmlContent = md.render(response);

    // 这里你可以在现有内容的基础上追加新的分析结果
    const updatedContent = `<div class="markdown-body">${htmlContent}</div>`;

    // 更新面板内容
    panel.webview.html = updatedContent;
}

// This method is called when your extension is deactivated

export function deactivate() {}
