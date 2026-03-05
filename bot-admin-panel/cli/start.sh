#!/bin/bash

# Ensure tmux is installed
if ! command -v tmux &> /dev/null
then
    echo "tmux could not be found, please install it (e.g., sudo apt-get install tmux)"
    exit 1
fi

SESSION_NAME="bot_manager"

# Kill existing tmux session if it's running
tmux has-session -t ${SESSION_NAME} 2>/dev/null
if [ $? == 0 ]; then
    echo "Killing existing tmux session: ${SESSION_NAME}"
    tmux kill-session -t ${SESSION_NAME}
    sleep 1 # Give it a moment to tear down
fi

echo "Starting tmux session: ${SESSION_NAME}"
tmux new-session -d -s ${SESSION_NAME}

# Pane 0: Python Bot Engine (Flask Server) - serves UI and API
tmux rename-window -t ${SESSION_NAME}:0 "Bot Engine + Dashboard API"
tmux send-keys -t ${SESSION_NAME}:0 "cd /home/nestorfabianriveros2014/bot-manager/bot-engine" C-m
tmux send-keys -t ${SESSION_NAME}:0 "source venv/bin/activate" C-m
tmux send-keys -t ${SESSION_NAME}:0 "python3 server.py" C-m

# Pane 1: Placeholder / Monitoring
tmux split-window -h -t ${SESSION_NAME}:0
tmux select-pane -t ${SESSION_NAME}:1
tmux send-keys -t ${SESSION_NAME}:1 "echo 'Monitoring Flask (Bot Engine) output...'" C-m
tmux send-keys -t ${SESSION_NAME}:1 "echo 'Access Dashboard at https://api.fundacionidear.com/'" C-m
tmux send-keys -t ${SESSION_NAME}:1 "tail -f /home/nestorfabianriveros2014/bot-manager/bot-engine/logs/conversations.log" C-m


# Attach to the tmux session
echo "Attaching to tmux session. Use Ctrl+b then arrow keys to navigate panes."
echo "Use Ctrl+b d to detach from the session."
tmux attach-session -t ${SESSION_NAME}