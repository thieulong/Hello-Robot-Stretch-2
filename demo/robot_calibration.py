import stretch_body.robot

r = stretch_body.robot.Robot()

if not r.startup():
    exit()

if not r.calibrated():
    r.home()

r.arm.pretty_print()
r.lift.pretty_print()
r.base.pretty_print()
r.head.pretty_print()
r.end_of_arm.pretty_print()

r.wacc.pretty_print()
r.pimu.pretty_print()

r.get_status()
r.stop()
