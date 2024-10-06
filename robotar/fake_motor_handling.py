"""Display motor commands on systems without motors, for debugging."""
from displayarray import display

def get_display_motor_handling():
    d = display()
    def motor_handling(tensor_buffer):
        pwms = tensor_buffer.tensors[0]
        d.update(pwms, 'motor_tensor')
    return motor_handling
