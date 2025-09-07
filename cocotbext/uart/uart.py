"""

Copyright (c) 2020-2025 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

import logging

import cocotb
from cocotb.queue import Queue
from cocotb.triggers import FallingEdge, Timer, First, Event

from .version import __version__


class UartSource:
    def __init__(self, data, baud=9600, bits=8, stop_bits=1, *args, **kwargs):
        self.log = logging.getLogger(f"cocotb.{data._path}")
        self._data = data
        self._baud = baud
        self._bits = bits
        self._stop_bits = stop_bits

        self.log.info("UART source")
        self.log.info("cocotbext-uart version %s", __version__)
        self.log.info("Copyright (c) 2020-2025 Alex Forencich")
        self.log.info("https://github.com/alexforencich/cocotbext-uart")

        super().__init__(*args, **kwargs)

        self.active = False
        self.queue = Queue()

        self._idle = Event()
        self._idle.set()

        self._data.setimmediatevalue(1)

        self.log.info("UART source configuration:")
        self.log.info("  Baud rate: %d bps", self._baud)
        self.log.info("  Byte size: %d bits", self._bits)
        self.log.info("  Stop bits: %f bits", self._stop_bits)

        self._run_cr = None
        self._restart()

    def _restart(self):
        if self._run_cr is not None:
            self._run_cr.kill()
        self._run_cr = cocotb.start_soon(self._run(self._data, self._baud, self._bits, self._stop_bits))

    @property
    def baud(self):
        return self._baud

    @baud.setter
    def baud(self, value):
        self.baud = value
        self._restart()

    @property
    def bits(self):
        return self._bits

    @bits.setter
    def bits(self, value):
        self.bits = value
        self._restart()

    @property
    def stop_bits(self):
        return self._stop_bits

    @stop_bits.setter
    def stop_bits(self, value):
        self.stop_bits = value
        self._restart()

    async def write(self, data):
        for b in data:
            await self.queue.put(int(b))
            self._idle.clear()

    def write_nowait(self, data):
        for b in data:
            self.queue.put_nowait(int(b))
        self._idle.clear()

    def count(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def idle(self):
        return self.empty() and not self.active

    def clear(self):
        while not self.queue.empty():
            _ = self.queue.get_nowait()

    async def wait(self):
        await self._idle.wait()

    async def _run(self, data, baud, bits, stop_bits):
        self.active = False

        bit_t = Timer(int(1e9/self.baud), 'ns')
        stop_bit_t = Timer(int(1e9/self.baud*stop_bits), 'ns')

        while True:
            if self.empty():
                self.active = False
                self._idle.set()

            b = await self.queue.get()
            self.active = True

            self.log.info("Write byte 0x%02x", b)

            # start bit
            data.value = 0
            await bit_t

            # data bits
            for k in range(self.bits):
                data.value = b & 1
                b >>= 1
                await bit_t

            # stop bit
            data.value = 1
            await stop_bit_t


class UartSink:

    def __init__(self, data, baud=9600, bits=8, stop_bits=1, *args, **kwargs):
        self.log = logging.getLogger(f"cocotb.{data._path}")
        self._data = data
        self._baud = baud
        self._bits = bits
        self._stop_bits = stop_bits

        self.log.info("UART sink")
        self.log.info("cocotbext-uart version %s", __version__)
        self.log.info("Copyright (c) 2020-2025 Alex Forencich")
        self.log.info("https://github.com/alexforencich/cocotbext-uart")

        super().__init__(*args, **kwargs)

        self.active = False
        self.queue = Queue()
        self.sync = Event()

        self.log.info("UART sink configuration:")
        self.log.info("  Baud rate: %d bps", self._baud)
        self.log.info("  Byte size: %d bits", self._bits)
        self.log.info("  Stop bits: %f bits", self._stop_bits)

        self._run_cr = None
        self._restart()

    def _restart(self):
        if self._run_cr is not None:
            self._run_cr.kill()
        self._run_cr = cocotb.start_soon(self._run(self._data, self._baud, self._bits, self._stop_bits))

    @property
    def baud(self):
        return self._baud

    @baud.setter
    def baud(self, value):
        self.baud = value
        self._restart()

    @property
    def bits(self):
        return self._bits

    @bits.setter
    def bits(self, value):
        self.bits = value
        self._restart()

    @property
    def stop_bits(self):
        return self._stop_bits

    @stop_bits.setter
    def stop_bits(self, value):
        self.stop_bits = value
        self._restart()

    async def read(self, count=-1):
        while self.empty():
            self.sync.clear()
            await self.sync.wait()
        return self.read_nowait(count)

    def read_nowait(self, count=-1):
        if count < 0:
            count = self.queue.qsize()
        if self.bits == 8:
            data = bytearray()
        else:
            data = []
        for k in range(count):
            data.append(self.queue.get_nowait())
        return data

    def count(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def idle(self):
        return not self.active

    def clear(self):
        while not self.queue.empty():
            _ = self.queue.get_nowait()

    async def wait(self, timeout=0, timeout_unit='ns'):
        if not self.empty():
            return
        self.sync.clear()
        if timeout:
            await First(self.sync.wait(), Timer(timeout, timeout_unit))
        else:
            await self.sync.wait()

    async def _run(self, data, baud, bits, stop_bits):
        self.active = False

        half_bit_t = Timer(int(1e9/self.baud/2), 'ns')
        bit_t = Timer(int(1e9/self.baud), 'ns')
        stop_bit_t = Timer(int(1e9/self.baud*stop_bits), 'ns')

        while True:
            await FallingEdge(data)

            self.active = True

            # start bit
            await half_bit_t

            # data bits
            b = 0
            for k in range(bits):
                await bit_t
                b |= bool(int(data.value)) << k

            # stop bit
            await stop_bit_t

            self.log.info("Read byte 0x%02x", b)

            self.queue.put_nowait(b)
            self.sync.set()

            self.active = False
