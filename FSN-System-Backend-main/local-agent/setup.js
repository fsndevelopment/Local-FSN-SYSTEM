#!/usr/bin/env node

/**
 * FSN Local Agent Setup Script
 * Installs dependencies and configures the local agent
 */

const { exec, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const question = (query) => new Promise((resolve) => rl.question(query, resolve));

class SetupAgent {
    constructor() {
        this.config = {
            backendUrl: '',
            logLevel: 'info'
        };
    }

    async run() {
        console.log('🚀 FSN Local Agent Setup');
        console.log('========================\n');

        try {
            await this.checkPrerequisites();
            await this.gatherConfiguration();
            await this.installDependencies();
            await this.createConfigFile();
            await this.createStartScripts();
            
            console.log('\n✅ Setup completed successfully!');
            console.log('\n📋 Next steps:');
            console.log('1. Connect your phone via USB');
            console.log('2. Enable Developer Mode on your phone');
            console.log('3. Trust your computer on the phone');
            console.log('4. Run: npm start');
            console.log('\n🌐 Your phone will be accessible from your cloud backend!');

        } catch (error) {
            console.error('❌ Setup failed:', error.message);
            process.exit(1);
        } finally {
            rl.close();
        }
    }

    async checkPrerequisites() {
        console.log('🔍 Checking prerequisites...');

        const checks = [
            { name: 'Node.js', command: 'node --version' },
            { name: 'npm', command: 'npm --version' },
            { name: 'Appium', command: 'appium --version' }
        ];

        for (const check of checks) {
            try {
                await this.runCommand(check.command);
                console.log(`✅ ${check.name} is installed`);
            } catch (error) {
                console.log(`❌ ${check.name} is not installed`);
                
                if (check.name === 'Node.js') {
                    console.log('   Please install Node.js from https://nodejs.org/');
                } else if (check.name === 'npm') {
                    console.log('   npm should come with Node.js');
                } else if (check.name === 'Appium') {
                    console.log('   Installing Appium...');
                    await this.installAppium();
                }
            }
        }

        // Check for platform-specific tools
        if (process.platform === 'darwin') {
            await this.checkMacPrerequisites();
        } else if (process.platform === 'win32') {
            await this.checkWindowsPrerequisites();
        }
    }

    async checkMacPrerequisites() {
        const macChecks = [
            { name: 'Xcode Command Line Tools', command: 'xcode-select --version' },
            { name: 'Homebrew', command: 'brew --version' },
            { name: 'libimobiledevice', command: 'idevice_id --version' }
        ];

        for (const check of macChecks) {
            try {
                await this.runCommand(check.command);
                console.log(`✅ ${check.name} is installed`);
            } catch (error) {
                console.log(`❌ ${check.name} is not installed`);
                
                if (check.name === 'Xcode Command Line Tools') {
                    console.log('   Run: xcode-select --install');
                } else if (check.name === 'Homebrew') {
                    console.log('   Install from: https://brew.sh/');
                } else if (check.name === 'libimobiledevice') {
                    console.log('   Run: brew install libimobiledevice');
                }
            }
        }
    }

    async checkWindowsPrerequisites() {
        const windowsChecks = [
            { name: 'ADB', command: 'adb version' }
        ];

        for (const check of windowsChecks) {
            try {
                await this.runCommand(check.command);
                console.log(`✅ ${check.name} is installed`);
            } catch (error) {
                console.log(`❌ ${check.name} is not installed`);
                console.log('   Install Android SDK Platform Tools');
            }
        }
    }

    async installAppium() {
        try {
            console.log('📦 Installing Appium...');
            await this.runCommand('npm install -g appium');
            await this.runCommand('appium driver install uiautomator2');
            await this.runCommand('appium driver install xcuitest');
            console.log('✅ Appium installed successfully');
        } catch (error) {
            console.error('❌ Failed to install Appium:', error.message);
            throw error;
        }
    }

    async gatherConfiguration() {
        console.log('\n⚙️  Configuration');
        console.log('==================');

        this.config.backendUrl = await question('Enter your backend URL (e.g., https://your-backend.onrender.com): ');
        
        if (!this.config.backendUrl) {
            throw new Error('Backend URL is required');
        }

        // Validate URL format
        try {
            new URL(this.config.backendUrl);
        } catch (error) {
            throw new Error('Invalid URL format');
        }

        const logLevel = await question('Log level (info/debug/error) [info]: ');
        this.config.logLevel = logLevel || 'info';
    }

    async installDependencies() {
        console.log('\n📦 Installing dependencies...');
        
        try {
            await this.runCommand('npm install');
            console.log('✅ Dependencies installed successfully');
        } catch (error) {
            console.error('❌ Failed to install dependencies:', error.message);
            throw error;
        }
    }

    async createConfigFile() {
        console.log('\n📝 Creating configuration file...');
        
        const configContent = `module.exports = {
    BACKEND_URL: '${this.config.backendUrl}',
    LOG_LEVEL: '${this.config.logLevel}'
};`;

        fs.writeFileSync('config.js', configContent);
        console.log('✅ Configuration file created');
    }

    async createStartScripts() {
        console.log('\n📝 Creating start scripts...');

        // Create start script for different platforms
        if (process.platform === 'win32') {
            const startScript = `@echo off
echo Starting FSN Local Agent...
set BACKEND_URL=${this.config.backendUrl}
set LOG_LEVEL=${this.config.logLevel}
node agent.js
pause`;

            fs.writeFileSync('start.bat', startScript);
            console.log('✅ Created start.bat');
        } else {
            const startScript = `#!/bin/bash
echo "Starting FSN Local Agent..."
export BACKEND_URL="${this.config.backendUrl}"
export LOG_LEVEL="${this.config.logLevel}"
node agent.js`;

            fs.writeFileSync('start.sh', startScript);
            fs.chmodSync('start.sh', '755');
            console.log('✅ Created start.sh');
        }
    }

    runCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(stdout);
                }
            });
        });
    }
}

// Run setup
const setup = new SetupAgent();
setup.run().catch(error => {
    console.error('Setup failed:', error.message);
    process.exit(1);
});
