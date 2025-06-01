from machine import Pin, SPI
import time
from .core import calculate_regs, make_regs

adf4543_mux = Pin(12, Pin.IN, Pin.PULL_UP)
adf4543_le = Pin(13,Pin.OUT)
adf4543_clk = Pin(14,Pin.OUT)
adf4543_dat = Pin(15,Pin.OUT)

powerstatus = False
freq = 0

def get_locked():
    locked = True if adf4543_mux.value() else False
    return locked
    
def setfrequency(frequency_mhz, debug=False):
    global freq
    freq = frequency_mhz
    print(f"INFO: ADF4351 set to {freq:3.3f}MHz")
    setup_lo(debug)
    
def enable(debug=False):
    global powerstatus
    powerstatus=False
    setup_lo(debug)
    
def disable(debug=False):
    global powerstatus
    powerstatus=True
    setup_lo(debug)
    
def setup_lo(debug=False):
    global freq
    global powerstatus
    INT, MOD, FRAC, output_divider, band_select_clock_divider = calculate_regs(freq=freq)
    regs = make_regs(INT=INT, MOD=MOD, FRAC=FRAC, output_divider=output_divider, band_select_clock_divider=band_select_clock_divider,powerdown=powerstatus, mux_out=6)
    set_regs(regs)
    if debug:
        print_regs(regs)

def bstr_to_int(bstr):
    """ Convert a binary String into an int """
    i = 1
    outint = 0
    while len(bstr):
        if bstr[-1:] == '1':
            outint += int(1 * i)
        bstr = bstr[:-1]
        i = i * 2
    return outint

def register_decode_muxout(muxint):
    if muxint == 0:
        muxintstr = "Three-State-Output"
    elif muxint == 1:
        muxintstr = "DvDD"
    elif muxint == 2:
        muxintstr = "Dgnd"
    elif muxint == 3:
        muxintstr = "R-Counter-Output"
    elif muxint == 4:
        muxintstr = "N-Divider-Output"
    elif muxint == 5:
        muxintstr = "Analog-Lock-Detect"
    elif muxint == 6:
        muxintstr = "Digital-Locak-Detect"
    elif muxint == 7:
        muxintstr = "RESERVED"
    else:
        muxintstr = "INVALID"
    return f"MUXOutput:{muxintstr}({muxint})"    


def register_decode_r3clkdivmode(mode):
    if mode == 0:
        intstr = "ClockdividerOFF"
    elif mode == 1:
        intstr = "FastLockEnable"
    elif mode == 2:
        intstr = "ReSyncEnable"
    elif mode == 3:
        intstr = "RESERVED"
    else:
        intstr = f"INVALID:{mode}"
    return f"ClockDividerMode:{intstr}"    


def register_decode_r5ldpinmode(mode):
    if mode == 0:
        intstr = "LOW"
    elif mode == 1:
        intstr = "DigitalLockDetect"
    elif mode == 2:
        intstr = "LOW"
    elif mode == 3:
        intstr = "HIGH"
    else:
        intstr = f"INVALID:{mode}"
    return f"LockDetectPinOp:{intstr}"    

def register_decode_r4rfdivdr(select):
    if select == 0:
        intstr = "/1"
    elif select == 1:
        intstr = "/2"
    elif select == 2:
        intstr = "/4"
    elif select == 3:
        intstr = "/8"
    elif select == 4:
        intstr = "/16"
    elif select == 5:
        intstr = "/32"
    elif select == 6:
        intstr = "/64"
    elif select == 7:
        intstr = "RESERVED"
    else:
        intstr = f"INVALID:{select}"
    return f"RFDividerSelect:{intstr}"    

def register_decode_r4outputpower(mode):
    if mode == 0:
        intstr = "-4dBm"
    elif mode == 1:
        intstr = "-1dBm"
    elif mode == 2:
        intstr = "+2dBm"
    elif mode == 3:
        intstr = "+5dBm"
    else:
        intstr = f"INVALID:{mode}"
    return f"OutPutPower:{intstr}"    

def test_r2_chgpmpcur():
    for i in range(0,16):
        r2_chgpmpcur = 0.31 + (i * 0.313)
        print(f"{i}: {r2_chgpmpcur:.2f}")

def register_decode(regint):
    breg = f'{regint:0{32}b}'
    adf_reg = bstr_to_int(breg[-3:])
    if adf_reg == 0:
        r0_intval = bstr_to_int(breg[1:17])
        if r0_intval < 23:
            r0_intval = f"NOT_ALLOWED({r0_intval})"
        r0_fracval = bstr_to_int(breg[17:29])
        print(f"Register0: 16bitInt={r0_intval} 12bitFrac={r0_fracval}")
    elif adf_reg == 1:
        r1_phase = bstr_to_int(breg[3:4])
        r1_phasestr = "PhaseADJ:ON" if r1_phase else "PhaseADJ:OFF"
        r1_prescaler = bstr_to_int(breg[4:5])
        r1_prescalerstr = "Prescale:8/9" if r1_prescaler else "Prescale:4/5"
        r1_phase = bstr_to_int(breg[5:17])
        r1_modulos = bstr_to_int(breg[17:29])
        print(f"Register1: {r1_phasestr}({r1_phase}) {r1_prescalerstr}({r1_prescaler}) PhaseValue:{r1_phase} InterpolatorModulus:{r1_modulos}")
    elif adf_reg == 2:
        r2_noisemode = bstr_to_int(breg[1:3])
        if r2_noisemode == 0:
            r2_noisemodestr = "NoiseMode:LOW"
        elif r2_noisemode == 1:
            r2_noisemodestr = "NoiseMode:Reserved"
        elif r2_noisemode == 2:
            r2_noisemodestr = "NoiseMode:Reserved"
        elif r2_noisemode == 3:
            r2_noisemodestr = "NoiseMode:LowSpur"
        else:
            r2_noisemodestr = f"NoiseMode:INVALID({r2_noisemode})"
        r2_muxout = bstr_to_int(breg[3:6])
        r2_muxoutstr = register_decode_muxout(r2_muxout)
        r2_refdoublr = bstr_to_int(breg[6:7])
        r2_refdoublrstr = "RefDoubler:Enabled" if r2_refdoublr else "RefDoubler:Disabled"
        r2_refdivdr = bstr_to_int(breg[7:8])
        r2_refdivdrstr = "RefDivider:Enabled" if r2_refdivdr else "RefDivider:Disabled"
        r2_rcounter = bstr_to_int(breg[8:18])
        r2_doublbuf = bstr_to_int(breg[18:19])
        r2_doublbufstr = "RefDivider:Enabled" if r2_refdivdr else "RefDivider:Disabled"
        r2_chgpmpcur = 0.31 + (bstr_to_int(breg[19:23]) * 0.313)
        r2_chgpmpcurstr = f"ChargePumpCurrent:{r2_chgpmpcur:.2f}mA"
        r2_ldf = bstr_to_int(breg[23:24])
        r2_ldfstr = "LDF:Int-N" if r2_ldf else "LDF:Frac-N"
        r2_ldp = bstr_to_int(breg[24:25])
        r2_ldpstr = "LDP:6nS" if r2_ldf else "LDP:10nS"
        r2_dppol = bstr_to_int(breg[25:26])
        r2_dppolstr = "PDPol:Pos" if r2_dppol else "PDPol:Neg"
        r2_pwrdn = bstr_to_int(breg[26:27])
        r2_pwrdnstr = "PowerDown:Enabled" if r2_pwrdn else "PowerDown:Disabled"
        r2_cpthree = bstr_to_int(breg[27:28])
        r2_cpthreestr = "CP-ThreeState:Enabled" if r2_cpthree else "CP-ThreeState:Disabled"
        r2_cntrrst = bstr_to_int(breg[28:29])
        r2_cntrrststr = "CounterReset:Enabled" if r2_cntrrst else "CounterReset:Disabled"
        print(f"Register2: {r2_noisemodestr} {r2_muxoutstr} {r2_refdoublrstr} {r2_refdivdrstr}")
        print(f"Register2: RCounter:{r2_rcounter} {r2_chgpmpcurstr} {r2_ldfstr} {r2_ldpstr}")
        print(f"Register2: {r2_dppolstr} {r2_pwrdnstr} {r2_cpthreestr} {r2_cntrrststr}")
    elif adf_reg == 3:
        r3_bandslct = bstr_to_int(breg[8:9])
        r3_bandslctstr = "BandSelkectClockMode:HIGH" if r3_bandslct else "BandSelkectClockMode:LOW"
        r3_abp = bstr_to_int(breg[9:10])
        r3_abpstr = "AntiBacklashPW:3nS(Int-N)" if r3_abp else "AntiBacklashPW:6nS(Frac-N)"
        r3_chgcancel = bstr_to_int(breg[10:11])
        r3_chgcancelstr = "ChargeCancelation:Enabled" if r3_chgcancel else "ChargeCancelation:Disabled"
        r3_csr = bstr_to_int(breg[13:14])
        r3_csrstr = "CycleSlipReducion:Enabled" if r3_csr else "CycleSlipReducion:Disabled"
        r3_clkdivmode = bstr_to_int(breg[15:17])
        r3_clkdivmodestr = register_decode_r3clkdivmode(r3_clkdivmode)
        r3_clkdiv = bstr_to_int(breg[17:29])
        print(f"Register3: {r3_bandslctstr} {r3_abpstr} {r3_chgcancelstr}")
        print(f"Register3: {r3_csrstr} {r3_clkdivmodestr} ClockDivider:{r3_clkdiv}")
    elif adf_reg == 4:
        # UP TO HERE
        r4_fbslct = bstr_to_int(breg[8:9])
        r4_fbslctstr = "FeedBackSelect:Fundamental" if r4_fbslct else "FeedBackSelect:Divded"
        r4_rfdivdrsel = bstr_to_int(breg[9:12])
        r4_rfdivdrselstr = register_decode_r4rfdivdr(r4_rfdivdrsel)
        r4_banddivdr = bstr_to_int(breg[12:20])
        r4_vcopwrdn = bstr_to_int(breg[20:21])
        r4_vcopwrdnstr = "VCO-Powered:Down" if r4_vcopwrdn else "VCOPowered:Up"
        r4_mtld = bstr_to_int(breg[21:22])
        r4_mtldstr = "MuteTillLockDetected:Enabled" if r4_mtld else "MuteTillLockDetected:Disabled"
        r4_auxoutsel = bstr_to_int(breg[22:23])
        r4_auxoutselstr = "AuxOut:Fundamental" if r4_auxoutsel else "AuxOut:Divided"
        r4_auxoutenbl = bstr_to_int(breg[23:24])
        r4_auxoutenblstr = "AuxOut:Enabled" if r4_auxoutenbl else "AuxOut:Disabled"
        r4_auxoutpwr = bstr_to_int(breg[24:26])
        r4_auxoutpwrstr = register_decode_r4outputpower(r4_auxoutpwr)
        r4_rfoutenbl = bstr_to_int(breg[26:27])
        r4_rfoutenblstr = "AuxOut:Enabled" if r4_rfoutenbl else "AuxOut:Disabled"
        r4_rfoutpwr = bstr_to_int(breg[27:29])
        r4_rfoutpwrstr = register_decode_r4outputpower(r4_rfoutpwr)
        print(f"Register4: {r4_fbslctstr} {r4_rfdivdrselstr} BandClockDivider:{r4_banddivdr} {r4_vcopwrdnstr}")
        print(f"Register4: {r4_mtldstr} {r4_auxoutselstr} {r4_auxoutenblstr} Aux{r4_auxoutpwrstr}")
        print(f"Register4: {r4_rfoutenblstr} RF{r4_rfoutpwrstr}")
    elif adf_reg == 5:
        r5_ldpinmode = bstr_to_int(breg[8:10])
        r5_ldpinmodestr = register_decode_r5ldpinmode(r5_ldpinmode)
        print(f"Register5: {r5_ldpinmodestr}")
    else:
        print("Invalid Register")        
    barr = int_to_binarray(regint)
    carr = int_to_bytearray(regint)
    print(f"Register{adf_reg}: {barr} {carr} ({regint})")

def bitbangwrite(int):
    """ Will Bit bang a 32-bit word out """
    breg = f'{int:0{32}b}'
    adf4543_le.off()
    time.sleep(0.00002)
    for bit in breg:
        adf4543_clk.off()
        time.sleep(0.00002)
        if bit == '1':
            adf4543_dat.on()
        else:
            adf4543_dat.off()
        time.sleep(0.00001)
        adf4543_clk.on()
        time.sleep(0.00003)
    adf4543_clk.off()
    time.sleep(0.00003)
    adf4543_le.on()
    time.sleep(0.00004)
    adf4543_le.off()    


def int_to_binarray(binstring):
    """ WORKING """
    bin_array = []
    breg = f'{binstring:0{32}b}'
    while len(breg):
        bin_array.append(breg[:8])
        breg = breg[8:]
    return bin_array

def int_to_bytearray(binstring,bytelen=4):
    """ Convert Int into Byte Array of bytelen number of bytes"""
    barray = []
    breg = binstring
    while breg > 0:
        b2 = int(breg / 256)
        b3 = int(breg - (b2*256))
        barray.append(b3)
        breg = b2
    if len(barray) < bytelen:
        barray.append(0)
    return barray[::-1]

def set_regs(regs):
    i = 0
    for reg in regs:
        i += 1
        bitbangwrite(reg)        
        # write_data(device, buffer)

def print_regs(regs):
    for reg in regs:
        register_decode(reg)

def test_bstr_to_int():
    if bstr_to_int("1111111111") != 1023:
        print(f"ERROR - this should =1023 {bstr_to_int("1111111111")}")
    if bstr_to_int("1000000000000000") != 32768:
        print(f"ERROR - this should = 32768 {bstr_to_int("1000000000000000")}")
