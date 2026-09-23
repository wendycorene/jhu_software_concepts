"""Single-page Flask analysis with one background scrape at a time."""
import logging
import os
import threading
from datetime import datetime, timezone
from flask import Flask, redirect, render_template, url_for, jsonify
from sqlalchemy import select, func
from models import Applicant, Session
from orm_queries import run_queries
from presentation import QUESTIONS, format_result
from load_data import load_records
from scrape import scrape_data

# PostgreSQL advisory lock also coordinates multiple local Flask processes.
PULL_LOCK = 3062026


class PullManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.state = 'idle'
        self.message = 'Ready to check for new entries.'

    def running(self):
        if self.lock.locked():
            return True
        with Session() as session:
            acquired = session.scalar(select(func.pg_try_advisory_lock(PULL_LOCK)))
            if acquired:
                session.execute(select(func.pg_advisory_unlock(PULL_LOCK)))
            return not acquired

    def start(self):
        if not self.lock.acquire(blocking=False):
            return False
        self.state = 'running'
        self.message = 'New data is currently being retrieved. You can still refresh the analysis.'
        thread = threading.Thread(target=self._run, daemon=True)
        try:
            thread.start()
        except Exception:
            self.state = 'error'
            self.message = 'Could not start retrieval. Please try again.'
            self.lock.release()
            raise
        return True

    def _run(self):
        try:
            with Session() as session:
                acquired = session.scalar(select(func.pg_try_advisory_lock(PULL_LOCK)))
                if not acquired:
                    self.state = 'idle'
                    self.message = 'Another data pull is already running.'
                    return
                try:
                    known = set(session.scalars(select(Applicant.p_id)))
                    records = scrape_data(known_ids=known)
                    outcome = load_records(records)
                    self.state = 'success'
                    self.message = (f"Pull complete: {outcome['inserted']} new entries added; "
                                    f"{outcome['duplicates']} duplicates and {outcome['skipped']} unusable entries skipped. "
                                    'Select Update Analysis to refresh results.')
                finally:
                    session.execute(select(func.pg_advisory_unlock(PULL_LOCK)))
        except Exception:
            logging.exception('Data pull failed')
            self.state = 'error'
            self.message = 'Data could not be retrieved. Existing results are available; please try again later.'
        finally:
            self.lock.release()


def create_app(manager=None):
    app = Flask(__name__)
    manager = manager or PullManager()

    @app.get('/')
    def index():
        error, cards, running = None, [], False
        refreshed = None
        try:
            results = run_queries()
            cards = [{'number': n, 'question': QUESTIONS[n], 'answer': format_result(n, rows, results)}
                     for n, rows in results.items()]
            refreshed = datetime.now(timezone.utc).isoformat()
            running = manager.running()
        except Exception:
            app.logger.exception('Analysis query failed')
            error = 'The database is unavailable. Check the connection settings and run the data loader.'
        return render_template('analysis.html', cards=cards, running=running,
                               status=manager.message, error=error, state=manager.state, refreshed=refreshed)

    @app.get('/pull-status')
    def pull_status():
        try:
            running = manager.running()
            response = jsonify(running=running,
                state='running' if running else manager.state,
                message='Checking Grad Cafe for new entries...' if running else manager.message)
            response.headers['Cache-Control'] = 'no-store'
            return response
        except Exception:
            app.logger.exception('Status check failed')
            return jsonify(message='Cannot check progress right now. Retrying shortly.'), 503

    @app.post('/pull-data')
    def pull_data():
        manager.start()
        return redirect(url_for('index'), code=303)

    @app.post('/update-analysis')
    def update_analysis():
        return redirect(url_for('index'), code=303)

    return app


app = create_app()
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
