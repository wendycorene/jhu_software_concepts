// Poll only progress; analysis changes when the user selects Update Analysis.
const pullButton = document.querySelector('#pull-button');
const notice = document.querySelector('#pull-notice');
const message = document.querySelector('#pull-message');
const spinner = document.querySelector('#spinner');
const time = document.querySelector('time');
if (time) time.textContent = new Date(time.dateTime).toLocaleString();
let starting = false;
function display(status) {
    pullButton.disabled = status.running;
    spinner.hidden = !status.running;
    notice.dataset.state = status.state;
    message.textContent = status.message;
}
async function poll() {
    try {
        if (!starting) {
            const response = await fetch('/pull-status', {cache: 'no-store', signal: AbortSignal.timeout(10000)});
            if (!response.ok) throw new Error('Status unavailable');
            const status = await response.json();
            if (!starting) display(status);
        }
    } catch (error) {
        if (!starting) {
            spinner.hidden = true;
            notice.dataset.state = 'error';
            message.textContent = 'Cannot check progress right now. Retrying shortly.';
        }
    } finally {
        window.setTimeout(poll, 2500);
    }
}
document.querySelector('#pull-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (starting || pullButton.disabled) return;
    starting = true;
    display({running: true, state: 'running', message: 'Checking Grad Cafe for new entries...'});
    try {
        const response = await fetch(event.currentTarget.action, {method: 'POST', signal: AbortSignal.timeout(15000)});
        if (!response.ok) throw new Error('Unable to start');
    } catch (error) {
        display({running: true, state: 'error', message: 'Could not confirm retrieval started. Checking progress shortly...'});
        spinner.hidden = true;
    } finally {
        starting = false;
    }
});
document.querySelector('#update-form').addEventListener('submit', (event) => {
    const button = event.currentTarget.querySelector('button');
    button.disabled = true;
    button.textContent = 'Refreshing...';
    document.querySelector('#refresh-status').textContent = 'Refreshing analysis...';
});
poll();
