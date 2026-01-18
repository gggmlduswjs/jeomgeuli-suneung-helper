/**
 * 점자 디바이스 연결 카드
 * BLE 상태 및 배터리 표시
 */
import { useState, useEffect } from 'react';
import { Bluetooth, Battery, Wifi, WifiOff } from 'lucide-react';
import { useBrailleBLE } from '../../../hooks/useBrailleBLE';

interface BrailleDeviceCardProps {
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export default function BrailleDeviceCard({
  onConnect,
  onDisconnect
}: BrailleDeviceCardProps) {
  const { isConnected, batteryLevel, connect, disconnect } = useBrailleBLE();
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      await connect();
      if (onConnect) onConnect();
    } catch (error) {
      console.error('BLE 연결 실패:', error);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnect();
      if (onDisconnect) onDisconnect();
    } catch (error) {
      console.error('BLE 연결 해제 실패:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-2 border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Bluetooth
            className={`w-6 h-6 ${isConnected ? 'text-blue-600' : 'text-gray-400'}`}
          />
          <h3 className="text-lg font-semibold text-gray-800">점자 디바이스</h3>
        </div>
        {isConnected ? (
          <button
            onClick={handleDisconnect}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
            aria-label="디바이스 연결 해제"
          >
            연결 해제
          </button>
        ) : (
          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm disabled:opacity-50"
            aria-label="디바이스 연결"
          >
            {isConnecting ? '연결 중...' : '연결'}
          </button>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">연결 상태</span>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <>
                <Wifi className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-600">연결됨</span>
              </>
            ) : (
              <>
                <WifiOff className="w-5 h-5 text-gray-400" />
                <span className="text-sm font-medium text-gray-400">연결 안 됨</span>
              </>
            )}
          </div>
        </div>

        {isConnected && batteryLevel !== null && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">배터리</span>
            <div className="flex items-center gap-2">
              <Battery className="w-5 h-5 text-gray-600" />
              <span className="text-sm font-medium text-gray-800">
                {batteryLevel}%
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

