#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Monitor - Agendador de Execução Autônoma
Roda o orquestrador nos horários programados ao longo do dia,
sem necessidade de intervenção humana ou confirmações manuais.
"""

import time
import signal
import sys
import threading
from datetime import datetime
try:
    import schedule
except ImportError:
    schedule = None

from .config import (
    SCHEDULE_TIMES, SCHEDULE_INTERVAL_MINUTES, logger
)
from .orchestrator import LiveMonitorOrchestrator

_lock = threading.Lock()
_running = True

def handle_exit(signum, frame):
    """Trata encerramento gracioso do scheduler."""
    global _running
    logger.info(f"Sinal de interrupção recebido ({signum}). Encerrando agendador...")
    _running = False

def scheduled_job():
    """Tarefa executada a cada ciclo agendado."""
    if not _lock.acquire(blocking=False):
        logger.warning("Uma varredura anterior ainda está em andamento. Pulando este ciclo.")
        return
    try:
        logger.info(f"Iniciando ciclo agendado do Live Monitor às {datetime.now().strftime('%H:%M:%S')}...")
        orchestrator = LiveMonitorOrchestrator()
        result = orchestrator.run_scan()
        logger.info(f"Ciclo concluído. Resultados: {result}")
    except Exception as e:
        logger.error(f"Erro na execução do ciclo agendado: {e}", exc_info=True)
    finally:
        _lock.release()

def start_scheduler():
    """Inicia o agendador em loop infinito."""
    global _running
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    logger.info("Configurando rotinas do agendador Live Monitor...")

    # Executa uma varredura imediatamente na inicialização
    scheduled_job()

    if schedule:
        if SCHEDULE_INTERVAL_MINUTES > 0:
            logger.info(f"Modo Intervalo Ativo (via schedule): varredura a cada {SCHEDULE_INTERVAL_MINUTES} minutos.")
            schedule.every(SCHEDULE_INTERVAL_MINUTES).minutes.do(scheduled_job)
        else:
            logger.info(f"Modo Horários Fixos Ativo: {SCHEDULE_TIMES}")
            for t in SCHEDULE_TIMES:
                t_clean = t.strip()
                if t_clean:
                    try:
                        schedule.every().day.at(t_clean).do(scheduled_job)
                        logger.info(f" - Agendado para {t_clean} diariamente")
                    except Exception as e:
                        logger.error(f"Formato de horário inválido '{t_clean}': {e}")

        logger.info("Agendador em execução em segundo plano. Pressione Ctrl+C para parar.")
        while _running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Erro no loop do agendador: {e}")
                time.sleep(5)
    else:
        logger.info("Pacote 'schedule' não instalado. Utilizando relógio nativo em loop.")
        interval_secs = (SCHEDULE_INTERVAL_MINUTES * 60) if SCHEDULE_INTERVAL_MINUTES > 0 else 1800
        last_check_min = ""
        while _running:
            try:
                now = datetime.now()
                current_hm = now.strftime("%H:%M")
                if SCHEDULE_INTERVAL_MINUTES > 0:
                    time.sleep(interval_secs)
                    scheduled_job()
                else:
                    if current_hm in [t.strip() for t in SCHEDULE_TIMES] and current_hm != last_check_min:
                        last_check_min = current_hm
                        scheduled_job()
                    time.sleep(20)
            except Exception as e:
                logger.error(f"Erro no loop do agendador nativo: {e}")
                time.sleep(10)

    logger.info("Agendador Live Monitor finalizado com sucesso.")

if __name__ == "__main__":
    start_scheduler()
