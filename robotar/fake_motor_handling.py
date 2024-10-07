"""Display motor commands on systems without motors, for debugging."""
from displayarray import display
import numpy as np
def get_display_motor_handling():
    d = display()
    def motor_handling(tensor_buffer):
        pwms = tensor_buffer.tensors[0]
        pwms = pwms.reshape(pwms.shape[0],1)
        d.update(pwms, 'motor_tensor')
    return motor_handling

if __name__=='__main__':
    g = get_display_motor_handling()
    class hi:
        tensors = None
    h = hi()
    h.tensors = np.random.random([8]).astype(np.float32)
    for _ in range(100):
        g(h)