from Framework3.Framework import parent_framework_start, child_framework_start, start_process
from Framework3.Thread import FThread
from time import sleep
from queue import Empty
from monotonic import monotonic as timer
from Framework3.Message import Message, LogMessage
from Framework3.Constants import INFO, DEBUG, ERROR, CRITICAL, MONITOR
from Framework3.FRouter import send_request, send_response, send_log_message, send_message


def init_c(arg, common):
    arg['in_queue'] = common['c_queue']
    arg['count_timer'] = int(timer())
    arg['count'] = 0
    arg['monit_message'] = Message(destination=MONITOR, subject='C_message')
    arg['monit_timer'] = timer()
    return None


def main_c(arg, common):
    try:
        temp_message = arg['in_queue'].get(timeout=1)
        #print 'Main_c received', temp_message
        log_message = LogMessage(log_level=INFO, log_message='C message', log_details=temp_message.data)
        send_log_message(arg, common, log_message)
        response_message = Message(data=timer()-temp_message.data)
        send_response(common, temp_message, response_message)
        if int(timer()) !=  arg['count_timer']:
            print(arg['count'])
            arg['count_timer'] = int(timer())
            arg['count'] = 0
        else:
            arg['count'] += 1
    except Empty:
        print('main_c')

    if timer() > arg['monit_timer']:
        send_message(common, arg['monit_message'])
        arg['monit_timer'] = timer() + 2
        
    return None


def exit_c(arg, common):
    return None


def init_s(arg, common):
    arg['timer'] = timer()
    arg['monit_message'] = Message(destination=MONITOR, subject='S_message')
    arg['monit_timer'] = timer()
    return None


def main_s(arg, common):
    if timer() > arg['timer']:
        arg['timer'] = timer()
        message = Message(destination=b'C', data=timer(), skip_serialize=True, timeout=1)
        result = send_request(common, message)
        #temp = result.retrieve()
        #print 'S received', [temp]
    if timer() > arg['monit_timer']:
        send_message(common, arg['monit_message'])
        arg['monit_timer'] = timer() + 2
    sleep(0.0001)
    return None


def exit_s(arg, common):
    return None



def c_process(args, log_level):
    local_addresses = {b'C':'c_queue'}
    expected_messages={'C_message':3}
    common = child_framework_start(args['router_address'], args['router_id'], args['process_name']
                                   , local_addresses, log_level, expected_messages=expected_messages)
    
    
    c_args = {}
    temp = FThread(init_c, main_c, exit_c, c_args, common, daemon=False
                , thread_name='C_Thread', ignore_shutdown=False)
    
    while True:
        sleep(1)
    
    return None


def s_process(args, log_level):
    local_addresses = {b'S':'s_queue'}
    expected_messages={'S_message':3}
    common = child_framework_start(args['router_address'], args['router_id'], args['process_name']
                                   , local_addresses, log_level, expected_messages=expected_messages)
    
    s_args = {}
    temp = FThread(init_s, main_s, exit_s, s_args, common, daemon=False
                , thread_name='S_Thread', ignore_shutdown=False)
    
    
    while True:
        sleep(1)
    
    return None

if __name__ == '__main__':
    local_addresses = {}
    child_router_ids = [b'Child1', b'Child2']
    child_router_addresses = ['tcp://127.0.0.1:8788', 'tcp://127.0.0.1:8789']
    common = parent_framework_start(child_router_ids, child_router_addresses, local_addresses, logging_level=DEBUG)
    
    c_proc_args = {'process_name':'Child Process1', 'router_address':'tcp://127.0.0.1:8788'
                 , 'router_id':b'Child1'}
    start_process(c_process, c_proc_args, common)

    s_proc_args = {'process_name':'Child Process2', 'router_address':'tcp://127.0.0.1:8789'
                 , 'router_id':b'Child2'}
    start_process(s_process, s_proc_args, common)
    
    while True:
        sleep(1)