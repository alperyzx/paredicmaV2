#!/bin/bash

echo "Starting Paredicma - Redis Cluster Management Tool..."

# Function to find the highest Python 3.x version available
find_latest_python() {
    if command -v python3 &>/dev/null; then
        python_cmd="python3"
    elif command -v python &>/dev/null; then
        python_version=$(python --version 2>&1)
        if [[ $python_version == Python\ 3* ]]; then
            python_cmd="python"
        else
            echo "No Python 3.x installation found. Please install Python 3.6 or higher."
            exit 1
        fi
    else
        echo "No Python installation found. Please install Python 3.6 or higher."
        exit 1
    fi

    # Display detected Python version
    python_full_version=$($python_cmd --version 2>&1 | awk '{print $2}')
    echo "Using $python_cmd (version $python_full_version)"

    echo $python_cmd
}

# Check and install required packages
check_and_install_packages() {
    local python_cmd=$1
    local required_packages=("fastapi" "uvicorn")
    local missing_packages=()

    echo "Checking required packages..."

    for package in "${required_packages[@]}"; do
        if ! $python_cmd -c "import $package" &>/dev/null; then
            missing_packages+=("$package")
        fi
    done

    if [ ${#missing_packages[@]} -eq 0 ]; then
        echo "All required packages are installed."
    else
        echo "Installing missing packages: ${missing_packages[*]}"

        # Check for pip
        if command -v pip3 &>/dev/null; then
            pip_cmd="pip3"
        elif command -v pip &>/dev/null; then
            pip_cmd="pip"
        else
            echo "pip not found. Installing pip..."
            if [ -f /etc/debian_version ]; then
                # Debian/Ubuntu
                sudo apt update && sudo apt install -y python3-pip
            elif [ -f /etc/redhat-release ]; then
                # RHEL/CentOS/Fedora
                sudo yum install -y python3-pip
            else
                echo "Please install pip manually and try again."
                exit 1
            fi
            pip_cmd="pip3"
        fi

        # Install missing packages
        $pip_cmd install "${missing_packages[@]}"
        echo "Package installation complete."
    fi
}

# Check for virtual environment and use it if available
if [ -d ".venv" ]; then
    echo "Virtual environment found. Activating..."

    # Different activation files based on OS
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        PYTHON_CMD="python"
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
        PYTHON_CMD="python"
    else
        echo "Virtual environment found but activation script not located."
        echo "Falling back to system Python..."
        PYTHON_CMD=$(find_latest_python)
    fi

    # Verify virtual environment is active
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo "Using virtual environment at: $VIRTUAL_ENV"
    else
        echo "Failed to activate virtual environment. Falling back to system Python..."
        PYTHON_CMD=$(find_latest_python)
    fi
else
    echo "No virtual environment found. Using system Python..."
    PYTHON_CMD=$(find_latest_python)
fi

# Check and install packages (only if not using venv)
if [[ "$VIRTUAL_ENV" == "" ]]; then
    check_and_install_packages $PYTHON_CMD
fi

# Run the application
echo "Launching Paredicma Web Interface..."
$PYTHON_CMD parewebMon.py

exit $?