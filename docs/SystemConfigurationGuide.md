## Configuring a Windows Development Environment for TIMES-NZ

This guide provides instructions for setting up a Windows development environment for TIMES-NZ. It includes the following steps:
1. Install Anaconda
2. Install Chocolatey
3. Install Git for Windows and Unix-like Utilities with Chocolatey
4. Enable WSL 2 (Windows Subsystem for Linux version 2)
5. Install Docker Desktop
6. Configure SSH for Git
7. Install Visual Studio Code
8. Install Python Extension for Visual Studio Code
9. Install GAMS
10. Install VEDA-FE
11. Clone the TIMES-NZ Repository and associated repositories


#### Step 1: Install Anaconda

Click `Windows icon` -> type `Anaconda` -> click `Downloads Anaconda`
Install just for user - this defaulted to `C:\Users\<User>\AppData\Local\Anaconda3`

Pin "Anaconda Powershell Prompt" to taskbar

To make the Command Prompt or PowerShell environment on your colleague's Windows machine more like Bash, including adding the which command and other Unix-like utilities, you can install Chocolatey and use it to install packages that provide these functionalities. Chocolatey is a package manager for Windows, akin to apt or yum on Linux, that simplifies the process of managing software.

#### Step 2: Install Chocolatey

Open PowerShell as Administrator: Press Windows + X and select "Windows PowerShell (Admin)" or "Command Prompt (Admin)" from the menu.

Execute the following command in the PowerShell window:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
```

This command downloads and runs the Chocolatey installation script.

Close and Reopen PowerShell: Once the installation is complete, close the PowerShell window and reopen it to refresh the environment and recognize Chocolatey commands.

#### Step 3: Install Unix-like Utilities with Chocolatey

With Chocolatey installed, you can now install various Unix-like utilities, including those that provide a which command functionality.

Open PowerShell as Administrator again.

Install Git for Windows and GNU on Windows by running:
```powershell
choco install git -y
choco install gow -y
```

Other potentially useful packages include gnuwin and utililies like wget:
```powershell
choco install gnuwin -y
choco install wget -y
```

#### Step 4: Enable WSL 2 (Windows Subsystem for Linux version 2)
Open PowerShell as Administrator and run the following command to install Ubuntu:
```
wsl --install Ubuntu
```
This will probably require a system restart, followed by configuration of Ubuntu. Use your windows username and password.

Open PowerShell as Administrator and run the following command to enable WSL:
```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

Enable the Virtual Machine Platform feature with this command:
```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

Set WSL 2 as your default version with this command:
```powershell
wsl --set-default-version 2
```

Restart your computer.

#### Step 5: Install Docker Desktop

Download and install Docker Desktop from the Docker website: https://www.docker.com/products/docker-desktop

Restart your computer.

Confirm that docker has installed correctly by running the following command in PowerShell:
```powershell
docker images
```
This will probably require you to start Docker Desktop, in order to start the Docker engine running in the background.

#### Step 6: Configure SSH for Git

First confirm that you have an SSH key by running the following command in PowerShell:
```powershell
ls -la ~/.ssh
```

If you don't have an SSH key, generate one by running the following command in PowerShell:
```powershell
ssh-keygen -t rsa -b 4096
```

Copy the SSH key to the clipboard by running the following command in PowerShell:
```powershell
cat ~/.ssh/id_rsa.pub | clip
```

Navigate to your GitHub account settings and click on "SSH and GPG keys" in the left-hand menu. Click on "New SSH key" and paste the key into the "Key" field. Click "Add SSH key".

#### Step 7: Install Visual Studio Code

Download and install Visual Studio Code from the Visual Studio Code website: https://code.visualstudio.com/

#### Step 8: Install Python Extension for Visual Studio Code

Open Visual Studio Code and click on the Extensions icon in the Activity Bar on the side of the window. Search for "Python" and click "Install" on the Python extension by Microsoft.

#### Step 9: Install GAMS

Download and install GAMS from the GAMS website: https://www.gams.com/download/

#### Step 10: Install VEDA-FE

Navigate to https://github.com/kanors-emr/Veda2.0-Installation?tab=readme-ov-file
Follow the links to "Download and install prerequisites"
Follow the link to "download localhost"
Unzip the files into your home directory (C:\Users\<User>\Veda).

#### Step 11: Clone the TIMES-NZ Repository and associated repositories

Open the Anaconda Powershell Prompt and navigate to the directory where you want to clone the TIMES-NZ repository. Clone the repositories by running the following commands:
```powershell
git clone git@github.com:EECA-NZ/TIMES-NZ-Model-Files
git clone git@github.com:EECA-NZ/TIMES-NZ-GAMS-Files.git
git clone git@github.com:EECA-NZ/TIMES-NZ-Visualisation.git
git clone git@github.com:EECA-NZ/TIMES-NZ-internal-guide-EECA.git
```

You should now have a Windows development environment set up for TIMES-NZ.

