import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles


segments = [ 63, 6, 91, 79, 102, 109, 124, 7, 127, 103 ]

@cocotb.test()
async def test_loopback_ericsmi(dut):
    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # reset
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut._log.info("reset")
    dut.rst_n.value = 0
    # set the compare value
    await ClockCycles(dut.clk, 2)

    # Test the default loopback, which works in reset

    dut.ui_in.value = 0xF0
    await ClockCycles(dut.clk, 1)
    assert 0x80 & int(dut.uo_out.value) == 0x80
    dut.ui_in.value = 0xE0
    await ClockCycles(dut.clk, 1)
    assert 0x80 & int(dut.uo_out.value) == 0x00

    dut._log.info("PASS: &ui_in[7:4]")

    for i in range(4):
        dut.ui_in.value = i
        await ClockCycles(dut.clk, 1)
        v = int(dut.uo_out.value)
        for j in range(7):
            assert 0x1 & v == 0x1 & i
            v >>= 1

    dut._log.info("PASS: buffer i[0]")

    dut.rst_n.value = 1

    for i in range(8):
        for j in range(8):
            if i != j:
                dut.ui_in.value = 0xF0
                dut.uio_in.value = 0x40 | (j<<3) | i
                await ClockCycles(dut.clk, 1)
                dut.ui_in.value = 0
                await ClockCycles(dut.clk, 1)
                assert dut.uio_in.value == dut.uio_out.value
                for k in range(2):
                    dut.ui_in.value = k << i
                    await ClockCycles(dut.clk, 1)
                    dut.ui_in.value = (k << i)|(1<<j)
                    await ClockCycles(dut.clk, 1)
                    assert k == 0x1 & int(dut.uo_out.value)

    dut._log.info("PASS: Race Bits")

    dut.ui_in.value = 0xF0
    # enable bypass and use sel0=1
    dut.uio_in.value = 0xC1
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 1)
    assert 0xC1 & int(dut.uio_out.value)

    for i in range(4):
        dut.ui_in.value = i
        await ClockCycles(dut.clk, 1)
        assert i & 0x1 == int(dut.uo_out.value) >> 6
        assert i >> 1 == 0x1 & int(dut.uo_out.value)

    dut._log.info("PASS: Bypass Mode")
