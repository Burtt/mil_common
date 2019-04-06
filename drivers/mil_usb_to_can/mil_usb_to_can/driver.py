#!/usr/bin/python
import rospy
from board import USBtoCANBoard
import importlib


class USBtoCANDriver(object):
    '''
    ROS Driver for the USB to CAN board.
    Allow users to specify a dictionary of device handle classes
    to be loaded at runtime to handle communication with specific devices.
    '''
    def __init__(self):
        port = rospy.get_param('~port', '/dev/tty0')
        baud = rospy.get_param('~baudrate', 9600)
        simulation = rospy.get_param('/is_simulation', True)
        # If simulation mode, load simualted devices
        if simulation:
            devices = {}
            for device_id, cls in self.parse_module_dictionary(rospy.get_param('~simulated_devices')):
                devices[device_id] = cls()
            self.board = USBtoCANBoard(port=port, baud=baud, simulated=simulation, devices=devices)
        else:
            self.board = USBtoCANBoard(port=port, baud=baud, simulated=simulation)

        # Add device handles from the modules specified in ROS params
        self.handles = []
        for device_id, cls in self.parse_module_dictionary(rospy.get_param('~device_handles')):
            self.handles.append(cls(self.board, device_id))

    @staticmethod
    def parse_module_dictionary(d):
        '''
        Generator to load classes from module strings specified in a dictionary
        Yields tulples (device_id, cls) of device_ids and their associeted imported class
        '''
        for device_id, module_name in d.iteritems():
            device_id = int(device_id)
            # Split module from class name
            module_name, cls = module_name.rsplit('.', 1)
            # import module
            module = importlib.import_module(module_name)
            # Yield a tuple (device_id, imported_class)
            yield device_id, getattr(module, cls)


if __name__ == '__main__':
    rospy.init_node('usb_to_can_driver')
    driver = USBtoCANDriver()
    rospy.spin()