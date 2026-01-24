// Web Bluetooth API type extensions
interface BluetoothDevice {
  name?: string;
  removeEventListener(
    type: string,
    listener: EventListenerOrEventListenerObject,
    options?: boolean | EventListenerOptions
  ): void;
}
