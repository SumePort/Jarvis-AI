import 'dart:async';
class DoomClient {
  final String deviceId;
  final String endpoint;
  Timer? _heartbeat;
  DoomClient(this.deviceId,this.endpoint);
  void start({Duration interval=const Duration(seconds:15)}) {
    _heartbeat=Timer.periodic(interval,(_)=>heartbeat());
  }
  Future<void> heartbeat() async { /* transport adapter supplied by app */ }
  void stop()=>_heartbeat?.cancel();
}
