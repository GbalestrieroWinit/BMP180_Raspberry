from smbus3 import SMBus
import time

BMP180_ADDR = 0x77

# Registri
REG_CONTROL = 0xF4
REG_RESULT = 0xF6
REG_CHIP_ID = 0xD0

# Comandi
CMD_TEMP = 0x2E
CMD_PRESSURE = 0x34


class BMP180:
    def __init__(self, bus_num=1, address=0x77, oss=3):
        self.bus = SMBus(bus_num)
        self.address = address
        self.oss = oss
        self._read_calibration()

    def _read_u16(self, reg):
        msb = self.bus.read_byte_data(self.address, reg)
        lsb = self.bus.read_byte_data(self.address, reg + 1)
        return (msb << 8) | lsb

    def _read_s16(self, reg):
        value = self._read_u16(reg)
        if value > 32767:
            value -= 65536
        return value

    def chip_id(self):
        return self.bus.read_byte_data(self.address, REG_CHIP_ID)

    def _read_calibration(self):
        self.AC1 = self._read_s16(0xAA)
        self.AC2 = self._read_s16(0xAC)
        self.AC3 = self._read_s16(0xAE)
        self.AC4 = self._read_u16(0xB0)
        self.AC5 = self._read_u16(0xB2)
        self.AC6 = self._read_u16(0xB4)
        self.B1  = self._read_s16(0xB6)
        self.B2  = self._read_s16(0xB8)
        self.MB  = self._read_s16(0xBA)
        self.MC  = self._read_s16(0xBC)
        self.MD  = self._read_s16(0xBE)

    def read_raw_temp(self):
        self.bus.write_byte_data(self.address, REG_CONTROL, CMD_TEMP)
        time.sleep(0.005)
        return self._read_u16(REG_RESULT)

    def read_raw_pressure(self):
        self.bus.write_byte_data(
            self.address,
            REG_CONTROL,
            CMD_PRESSURE + (self.oss << 6)
        )

        delays = {
            0: 0.005,
            1: 0.008,
            2: 0.014,
            3: 0.026
        }
        time.sleep(delays[self.oss])

        msb = self.bus.read_byte_data(self.address, REG_RESULT)
        lsb = self.bus.read_byte_data(self.address, REG_RESULT + 1)
        xlsb = self.bus.read_byte_data(self.address, REG_RESULT + 2)

        return ((msb << 16) | (lsb << 8) | xlsb) >> (8 - self.oss)

    def read(self):
        UT = self.read_raw_temp()
        UP = self.read_raw_pressure()

        # Temperatura compensata
        X1 = ((UT - self.AC6) * self.AC5) >> 15
        X2 = (self.MC << 11) // (X1 + self.MD)
        B5 = X1 + X2
        temperature = ((B5 + 8) >> 4) / 10.0

        # Pressione compensata
        B6 = B5 - 4000
        X1 = (self.B2 * ((B6 * B6) >> 12)) >> 11
        X2 = (self.AC2 * B6) >> 11
        X3 = X1 + X2
        B3 = (((self.AC1 * 4 + X3) << self.oss) + 2) >> 2

        X1 = (self.AC3 * B6) >> 13
        X2 = (self.B1 * ((B6 * B6) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self.AC4 * (X3 + 32768)) >> 15
        B7 = (UP - B3) * (50000 >> self.oss)

        if B7 < 0x80000000:
            p = (B7 * 2) // B4
        else:
            p = (B7 // B4) * 2

        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7357 * p) >> 16
        pressure = p + ((X1 + X2 + 3791) >> 4)

        return temperature, pressure

    def close(self):
        self.bus.close()


if __name__ == "__main__":
    sensor = BMP180(bus_num=1, address=0x77, oss=3)

    try:
        chip = sensor.chip_id()
        print(f"Chip ID: 0x{chip:02X}")

        while True:
            temp_c, press_pa = sensor.read()
            print(f"Temperatura: {temp_c:.2f} °C")
            print(f"Pressione:   {press_pa/100:.2f} hPa")
            print("-" * 30)
            time.sleep(2)

    except KeyboardInterrupt:
        pass
    finally:
        sensor.close()
