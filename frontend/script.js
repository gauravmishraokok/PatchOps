class Terminal {
    constructor() {
        this.output = document.getElementById('terminal-output');
        this.input = document.getElementById('terminal-input');
        this.isRunning = false;
        this.init();
    }

    init() {
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleCommand(this.input.value.trim());
                this.input.value = '';
            }
        });

        // Welcome message
        this.typeText(`
<span class="text-green">╔══════════════════════════════════════════════════════════════╗</span>
<span class="text-green">║</span> <span class="text-cyan">PatchOps Security Terminal v1.0 - Advanced Vulnerability Scanner</span> <span class="text-green">║</span>
<span class="text-green">║</span> <span class="text-gray">══════════════════════════════════════════════════════════════</span> <span class="text-green">║</span>
<span class="text-green">║</span> <span class="text-yellow">[SYSTEM]</span> <span class="text-white">Ready to analyze code for security vulnerabilities...</span> <span class="text-green">║</span>
<span class="text-green">║</span> <span class="text-gray">Type 'run' to initiate security analysis pipeline</span> <span class="text-green">║</span>
<span class="text-green">╚══════════════════════════════════════════════════════════════╝</span>

        `, 0);
    }

    handleCommand(command) {
        this.addLine(`<span class="prompt">$</span> ${command}`, 'text-white');
        
        if (command.toLowerCase() === 'run') {
            this.startSecurityAnalysis();
        } else if (command.toLowerCase() === 'clear') {
            this.clearTerminal();
        } else if (command.toLowerCase() === 'help') {
            this.showHelp();
        } else {
            this.addLine(`Command not recognized: ${command}`, 'text-red');
            this.addLine('Type "help" for available commands', 'text-gray');
        }
    }

    showHelp() {
        this.addLine('<span class="text-cyan">Available commands:</span>', 'text-cyan');
        this.addLine('  <span class="text-green">run</span>     - Start security analysis pipeline', 'text-white');
        this.addLine('  <span class="text-green">clear</span>   - Clear terminal', 'text-white');
        this.addLine('  <span class="text-green">help</span>    - Show this help message', 'text-white');
    }

    clearTerminal() {
        this.output.innerHTML = '';
    }

    addLine(text, className = 'text-green') {
        const line = document.createElement('div');
        line.className = className;
        line.innerHTML = text;
        this.output.appendChild(line);
        this.output.scrollTop = this.output.scrollHeight;
    }

    async typeText(text, delay = 50) {
        const lines = text.split('\n').filter(line => line.trim());
        for (const line of lines) {
            this.addLine(line);
            if (delay > 0) {
                await this.sleep(delay);
            }
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async startSecurityAnalysis() {
        if (this.isRunning) {
            this.addLine('<span class="text-yellow">[WARNING]</span> Analysis already in progress...', 'text-yellow');
            return;
        }

        this.isRunning = true;
        
        try {
            await this.simulateAnalysis();
        } catch (error) {
            this.addLine(`<span class="text-red">[ERROR]</span> ${error.message}`, 'text-red');
        } finally {
            this.isRunning = false;
            this.addLine('<span class="text-green">[SYSTEM]</span> Analysis complete. Ready for next command.', 'text-green');
        }
    }

    async simulateAnalysis() {
        // Phase 1: GitHub Fetch
        this.addLine('<span class="status-indicator status-running"></span><span class="text-yellow">[FETCH]</span> Connecting to GitHub repository...', 'text-yellow');
        await this.sleep(2000);
        this.addLine('<span class="status-indicator status-success"></span><span class="text-green">[FETCH]</span> Repository cloned: gauravmishraokok/PatchOps-Target', 'text-green');
        await this.sleep(1000);

        // Phase 2: File Reading
        this.addLine('<span class="status-indicator status-running"></span><span class="text-yellow">[READ]</span> Scanning source files...', 'text-yellow');
        await this.sleep(1500);
        this.addLine('<span class="status-indicator status-success"></span><span class="text-green">[READ]</span> Found target file: app.py (79 lines)', 'text-green');
        await this.sleep(1000);

        // Phase 3: Security Analysis
        this.addLine('<span class="status-indicator status-running"></span><span class="text-cyan">[ANALYZER]</span> Initializing security scanner...', 'text-cyan');
        await this.sleep(2000);
        
        // Show progress bar
        this.addLine('<div class="progress-bar"><div class="progress-fill" style="width: 0%"></div></div>', '');
        
        // Simulate different security checks
        const checks = [
            { name: 'Static Code Analysis', duration: 1000 },
            { name: 'Pattern Matching', duration: 800 },
            { name: 'Dependency Scanning', duration: 600 },
            { name: 'Configuration Analysis', duration: 700 },
            { name: 'Security Rules Engine', duration: 900 },
            { name: 'Vulnerability Database Lookup', duration: 500 },
            { name: 'Threat Modeling', duration: 1200 },
            { name: 'Exploitability Assessment', duration: 800 }
        ];

        for (let i = 0; i < checks.length; i++) {
            const check = checks[i];
            const progress = ((i + 1) / checks.length) * 100;
            
            this.addLine(`<span class="text-gray">  ├─</span> <span class="text-blue">${check.name}</span>`, 'text-blue');
            
            // Update progress bar
            const progressBar = this.output.querySelector('.progress-fill');
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            
            await this.sleep(check.duration);
        }

        this.addLine('<span class="status-indicator status-success"></span><span class="text-green">[ANALYZER]</span> Security analysis complete!', 'text-green');
        await this.sleep(1500);

        // Phase 4: Vulnerability Results
        this.addLine('<span class="text-cyan">[RESULTS]</span> Vulnerabilities discovered:', 'text-cyan');
        
        const vulnerabilities = [
            { type: 'Hardcoded Secrets', cwe: 'CWE-798', severity: 'CRITICAL' },
            { type: 'SQL Injection', cwe: 'CWE-89', severity: 'CRITICAL' },
            { type: 'Command Injection', cwe: 'CWE-78', severity: 'CRITICAL' },
            { type: 'Broken Access Control / IDOR', cwe: 'CWE-284', severity: 'HIGH' },
            { type: 'Unsafe Deserialization', cwe: 'CWE-502', severity: 'CRITICAL' }
        ];

        for (let i = 0; i < vulnerabilities.length; i++) {
            const vuln = vulnerabilities[i];
            const severityClass = vuln.severity === 'CRITICAL' ? 'text-red' : 'text-orange';
            const icon = vuln.severity === 'CRITICAL' ? '🔴' : '🟡';
            
            this.addLine(
                `<div class="vulnerability-item">
                    <span class="text-gray">  ${i + 1}.</span> 
                    <span class="${severityClass}">${icon} ${vuln.type}</span> 
                    <span class="text-gray">(${vuln.cwe})</span>
                    <span class="text-white">[${vuln.severity}]</span>
                </div>`, 
                ''
            );
            await this.sleep(300);
        }

        await this.sleep(2000);

        // Phase 5: Exploit Simulation
        this.addLine('<span class="status-indicator status-running"></span><span class="text-red">[EXPLOIT]</span> Simulating attack vectors...', 'text-red');
        await this.sleep(2000);
        
        const exploits = [
            'Testing SQL injection with payload: "1\' OR \'1\'=\'1"',
            'Attempting command injection: "; rm -rf /"',
            'Probing for deserialization attacks...',
            'Checking for hardcoded secret exposure...',
            'Testing IDOR bypass techniques...'
        ];

        for (const exploit of exploits) {
            this.addLine(`<span class="text-gray">  ├─</span> <span class="text-orange">${exploit}</span>`, 'text-orange');
            await this.sleep(800);
        }

        this.addLine('<span class="status-indicator status-success"></span><span class="text-green">[EXPLOIT]</span> All vulnerabilities confirmed exploitable!', 'text-green');
        await this.sleep(1500);

        // Phase 6: Patch Generation
        this.addLine('<span class="status-indicator status-running"></span><span class="text-purple">[PATCHER]</span> Generating security patches...', 'text-purple');
        await this.sleep(2500);
        
        this.addLine('<div class="progress-bar"><div class="progress-fill" style="width: 0%"></div></div>', '');
        
        for (let i = 0; i <= 100; i += 20) {
            const progressBar = this.output.querySelector('.progress-fill:last-of-type');
            if (progressBar) {
                progressBar.style.width = `${i}%`;
            }
            this.addLine(`<span class="text-gray">  ├─</span> <span class="text-purple">Applying patch ${i/20 + 1}/5...</span>`, 'text-purple');
            await this.sleep(500);
        }

        this.addLine('<span class="status-indicator status-success"></span><span class="text-green">[PATCHER]</span> All patches generated successfully!', 'text-green');
        await this.sleep(1500);

        // Phase 7: PR Creation
        this.addLine('<span class="status-indicator status-running"></span><span class="text-cyan">[GIT]</span> Creating pull request...', 'text-cyan');
        await this.sleep(2000);
        this.addLine('<span class="status-indicator status-success"></span><span class="text-green">[GIT]</span> PR created: https://github.com/gauravmishraokok/PatchOps-Target/pull/24', 'text-green');
        await this.sleep(1000);

        // Final Summary
        this.addLine(`
<span class="text-green">╔══════════════════════════════════════════════════════════════╗</span>
<span class="text-green">║</span> <span class="text-cyan">ANALYSIS SUMMARY</span> <span class="text-gray">═══════════════════════════════════════════════════</span> <span class="text-green">║</span>
<span class="text-green">║</span> <span class="text-white">• Vulnerabilities Found:</span> <span class="text-red">5</span> <span class="text-gray">(4 Critical, 1 High)</span> <span class="text-green">║</span>
<span class="text-green">║</span> <span class="text-white">• Vulnerabilities Fixed:</span> <span class="text-green">5/5</span> <span class="text-gray">(100% Success Rate)</span> <span class="text-green">║</span>
<span class="text-green">║</span> <span class="text-white">• LLM Calls Made:</span> <span class="text-blue">3</span> <span class="text-gray">(Analyzer → Patcher → PR Generator)</span> <span class="text-green">║</span>
<span class="text-green">║</span> <span class="text-white">• Pipeline Status:</span> <span class="text-green">✅ SUCCESS</span> <span class="text-gray">═══════════════════════════════════════</span> <span class="text-green">║</span>
<span class="text-green">╚══════════════════════════════════════════════════════════════╝</span>

        `, 0);

        // Add matrix rain effect
        this.createMatrixRain();
    }

    createMatrixRain() {
        const matrixBg = document.createElement('div');
        matrixBg.className = 'matrix-bg';
        document.body.appendChild(matrixBg);
        
        // Simple matrix rain effect
        const canvas = document.createElement('canvas');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.pointerEvents = 'none';
        canvas.style.opacity = '0.05';
        canvas.style.zIndex = '-1';
        
        const ctx = canvas.getContext('2d');
        const chars = '01';
        const fontSize = 14;
        const columns = canvas.width / fontSize;
        const drops = [];
        
        for (let i = 0; i < columns; i++) {
            drops[i] = 1;
        }
        
        function draw() {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.fillStyle = '#00ff00';
            ctx.font = fontSize + 'px monospace';
            
            for (let i = 0; i < drops.length; i++) {
                const text = chars[Math.floor(Math.random() * chars.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                
                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                    drops[i] = 0;
                }
                drops[i]++;
            }
        }
        
        matrixBg.appendChild(canvas);
        setInterval(draw, 33);
    }
}

// Initialize terminal when page loads
document.addEventListener('DOMContentLoaded', () => {
    new Terminal();
});
