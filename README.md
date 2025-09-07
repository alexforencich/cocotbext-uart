# UART interface modules for Cocotb

[![Regression Tests](https://github.com/alexforencich/cocotbext-uart/actions/workflows/regression-tests.yml/badge.svg)](https://github.com/alexforencich/cocotbext-uart/actions/workflows/regression-tests.yml)
[![codecov](https://codecov.io/gh/alexforencich/cocotbext-uart/branch/master/graph/badge.svg)](https://codecov.io/gh/alexforencich/cocotbext-uart)
[![PyPI version](https://badge.fury.io/py/cocotbext-uart.svg)](https://pypi.org/project/cocotbext-uart)
[![Downloads](https://pepy.tech/badge/cocotbext-uart)](https://pepy.tech/project/cocotbext-uart)

GitHub repository: https://github.com/alexforencich/cocotbext-uart

## Introduction

UART simulation models for [cocotb](https://github.com/cocotb/cocotb).

## Installation

Installation from pip (release version, stable):

    $ pip install cocotbext-uart

Installation from git (latest development version, potentially unstable):

    $ pip install https://github.com/alexforencich/cocotbext-uart/archive/master.zip

Installation for active development:

    $ git clone https://github.com/alexforencich/cocotbext-uart
    $ pip install -e cocotbext-uart

## Documentation and usage examples

See the `tests` directory, [taxi](https://github.com/fpganinja/taxi), and [verilog-uart](https://github.com/alexforencich/verilog-uart) for complete testbenches using these modules.

### UART

The `UartSource` and `UartSink` classes can be used to drive, receive, and monitor asynchronous serial data.

To use these modules, import the one you need and connect it to the DUT:

    from cocotbext.uart import UartSource, UartSink

    uart_source = UartSource(dut.rxd, baud=115200, bits=8)
    uart_sink = UartSink(dut.rxd, baud=115200, bits=8)

To send data into a design with a `UartSource`, call `write()` or `write_nowait()`.  Accepted data types are iterables of ints, including lists, bytes, bytearrays, etc.  Optionally, call `wait()` to wait for the transmit operation to complete.  Example:

    await uart_source.send(b'test data')
    # wait for operation to complete (optional)
    await uart_source.wait()

To receive data with a `UartSink`, call `read()` or `read_nowait()`.  Optionally call `wait()` to wait for new receive data.  `read()` will block until at least 1 data byte is available.  Both `read()` and `read_nowait()` will return up to _count_ bytes from the receive queue, or the entire contents of the receive queue if not specified.

    data = await uart_sink.recv()

#### Constructor parameters:

* _data_: data signal
* _baud_: baud rate in bits per second (optional, default 9600)
* _bits_: bits per byte (optional, default 8)
* _stop_bits_: length of stop bit in bit times (optional, default 1)

#### Attributes:

* _baud_: baud rate in bits per second
* _bits_: bits per byte
* _stop_bits_: length of stop bit in bit times

#### Methods

* `write(data)`: send _data_ (blocking) (source)
* `write_nowait(data)`: send _data_ (non-blocking) (source)
* `read(count)`: read _count_ bytes from buffer (blocking) (sink)
* `read_nowait(count)`: read _count_ bytes from buffer (non-blocking) (sink)
* `count()`: returns the number of items in the queue (all)
* `empty()`: returns _True_ if the queue is empty (all)
* `idle()`: returns _True_ if no transfer is in progress (all) or if the queue is not empty (source)
* `clear()`: drop all data in queue (all)
* `wait()`: wait for idle (source)
* `wait(timeout=0, timeout_unit='ns')`: wait for data received (sink)
