/**
 * 점자 디바이스 연결 카드
 * BLE 상태 및 배터리 표시
 */
import { useState, useEffect } from 'react';
import { Bluetooth, Battery, Wifi, WifiOff } from 'lucide-react';
import { useBrailleBLE } from '../../hooks/useBrailleBLE';

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
    <div className="bg-white rounded-lg shadow-md p-3 border-2 border-gray-200">
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2">
          <Bluetooth
            className={`w-5 h-5 ${isConnected ? 'text-blue-600' : 'text-gray-400'}`}
          />
          <h3 className="text-base font-semibold text-gray-800">점자 디바이스</h3>
        </div>
        {isConnected ? (
          <button
            onClick={handleDisconnect}
            className="px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-xs"
            aria-label="디바이스 연결 해제"
          >
            해제
          </button>
        ) : (
          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-xs disabled:opacity-50"
            aria-label="디바이스 연결"
          >
            {isConnecting ? '연결 중...' : '연결'}
          </button>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">연결 상태</span>
          <div className="flex items-center gap-1.5">
            {isConnected ? (
              <>
                <Wifi className="w-4 h-4 text-green-600" />
                <span className="text-xs font-medium text-green-600">연결됨</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-gray-400" />
                <span className="text-xs font-medium text-gray-400">연결 안 됨</span>
              </>
            )}
          </div>
        </div>

        {isConnected && batteryLevel !== null && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">배터리</span>
            <div className="flex items-center gap-1.5">
              <Battery className="w-4 h-4 text-gray-600" />
              <span className="text-xs font-medium text-gray-800">
                {batteryLevel}%
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

