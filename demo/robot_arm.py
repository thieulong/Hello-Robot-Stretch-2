import stretch_body.arm

a = stretch_body.arm.Arm()
a.motor.disable_sync_mode()
if not a.startup():
    exit() 

a.home()

starting_position = a.status['pos']

a.move_to(starting_position + 0.1)
a.push_command()
a.motor.wait_until_at_setpoint()

a.move_to(starting_position, v_m=0.2, a_m=0.25)
a.push_command()
a.motor.wait_until_at_setpoint()

a.move_by(0.1) 
a.push_command()
a.motor.wait_until_at_setpoint()

starting_position = a.status['pos']

# queue a trajectory consisting of four waypoints
a.trajectory.add(t_s=0, x_m=starting_position)
a.trajectory.add(t_s=3, x_m=0.15)
a.trajectory.add(t_s=6, x_m=0.1)
a.trajectory.add(t_s=9, x_m=0.2)

# trigger trajectory execution
a.follow_trajectory()
import time; time.sleep(9)
