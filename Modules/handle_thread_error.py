import Domoticz


def handle_thread_error( self, e):
    trace = []
    tb = e.__traceback__
    Domoticz.Error("'%s' failed '%s'" %(tb.tb_frame.f_code.co_name, str(e)))
    while tb is not None:
        trace.append(
            {
            "Module": tb.tb_frame.f_code.co_filename,
            "Function": tb.tb_frame.f_code.co_name,
            "Line": tb.tb_lineno
        })
        Domoticz.Error("----> Line %s in '%s', function %s" %( tb.tb_lineno, tb.tb_frame.f_code.co_filename,  tb.tb_frame.f_code.co_name,  ))
        tb = tb.tb_next


