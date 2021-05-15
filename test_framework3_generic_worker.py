from Framework3.Framework import parent_framework_start, child_framework_start, start_process
from Framework3.Thread import FThread, GenericWorkerFThread
from time import sleep
from monotonic import monotonic as timer
from Framework3.Message import Message, LogMessage
from Framework3.Constants import INFO, DEBUG, ERROR, CRITICAL, MONITOR
from Framework3.FRouter import send_request, send_response, send_log_message, send_message
from Framework3.util_queue import get_internal_messages


def init_c(arg, common):
    arg['in_queue'] = common['c_queue']
    arg['timer'] = timer()
    return None


def main_c(arg, common):
    if timer() > arg['timer']:
        work_message = Message(destination=b'S', data=timer(), skip_serialize=True, timeout=1)
        result = send_request(common, work_message)
        temp_message = result.get()
        print('Main_c received', temp_message)
        log_message = LogMessage(log_level=INFO, log_message='C message', log_details=temp_message.data)
        send_log_message(arg, common, log_message)
        arg['timer'] = timer() + 1
    sleep(0.1)
    return None


def exit_c(arg, common):
    return None


def main_s(arg, common):
    messages = get_internal_messages(arg)
    for message in messages:
        response_message = Message(data=arg['SELF'].thread_name)
        print('Main_S received', message)
        send_response(common, message, response_message)
    sleep(0.1)
    return None


def c_process(args, log_level):
    local_addresses = {b'C':'c_queue'}
    expected_messages={}
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
    expected_messages={}
    common = child_framework_start(args['router_address'], args['router_id'], args['process_name']
                                   , local_addresses, log_level, expected_messages=expected_messages)
    
    s_args = {'in_queue':common['s_queue']}
    for i in range(10):
        temp = GenericWorkerFThread(main_s, s_args, common, daemon=False
                    , thread_name='S_Thread %d' % (i+1), ignore_shutdown=False)
        sleep(0.05)
    
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