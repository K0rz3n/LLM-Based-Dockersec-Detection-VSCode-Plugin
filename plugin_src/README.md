# DockerSec Detection Plugin

DockerSec is a VS Code extension that enables one-click Dockerfile security risk detection and provides detailed explanations of the risk principles and corresponding remediation suggestions.
It’s designed to help developers efficiently address real-world security issues, enhance security awareness, and achieve true “security shift-left” in the development lifecycle.


## Usage guide

### Parameter Configuration

1.	Replace [Detector_Domain] in the source code with the domain name of the detect_server in your Plugin_server.

2.	Replace [Analyser_Domain] in the source code with the domain name of the analysis_server in your Plugin_server.

### Plugin Packaging and Installation

> vsce package
> code --install-extension dockersec-0.0.1.vsix

### Plugin Usage

Right-click on a Dockerfile, then select: [Check Dockerfile Security]



**Enjoy!**
