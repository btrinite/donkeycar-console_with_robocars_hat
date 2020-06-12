accesslog = 'gunicorn.access.log'
errorlog = 'gunicorn.log'
capture_output = True
timeout=180
access_log_format='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(T)s %(p)s'
# workers=4
threads=4