from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
from subprocess import check_output

import re
import signal

crlf_pat = re.compile(r'[\r\n]+')

class PrologKernel(Kernel):
    implementation = 'Prolog'
    implementation_version = '0.0.1'

    language_info = {
        'name': 'Prolog',
        'codemirror_mode': 'scheme',
        'mimetype': 'text/plain',
        'file_extension': '.pl'
    }

    _language_version = "1.3.0"


    @property
    def language_version(self):
        # if self._language_version is None:
        #     self._language_version = check_output(['prolog', '--version']).decode('utf-8')
        return self._language_version

    @property
    def banner(self):
        return u'Simple GNU Prolog Kernel (%s)' % self.language_version

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_prolog()

    def _start_prolog(self):
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            self.prologwrapper = replwrap.REPLWrapper("prolog", "| ?- ", None)
        finally:
            signal.signal(signal.SIGINT, sig)

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        code = crlf_pat.sub(' ', code.strip())
        if not code:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False
        try:
            output = self.prologwrapper.run_command(code, timeout=None)
        except KeyboardInterrupt:
            self.prologwrapper.child.sendintr()
            interrupted = True
            self.prologwrapper._expect_prompt()
            output = self.prologwrapper.child.before
        except EOF:
            output = self.prologwrapper.child.before + 'Restarting Prolog'
            self._start_prolog()

        if not silent:
            # Send standard output
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}

        return {'status': 'ok', 'execution_count': self.execution_count,
                'payload': [], 'user_expressions': {}}

# ===== MAIN =====
if __name__ == '__main__':
    from IPython.kernel.zmq.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=PrologKernel)
