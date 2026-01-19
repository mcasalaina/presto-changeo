/**
 * Audio utility functions for gpt-realtime voice integration
 *
 * gpt-realtime requires PCM16 format:
 * - 16-bit signed integers
 * - Little-endian byte order
 * - 24000 Hz sample rate
 * - Mono channel
 */

/**
 * Sample rate for gpt-realtime audio (24kHz)
 */
export const VOICE_SAMPLE_RATE = 24000

/**
 * Convert PCM16 base64 audio to Float32Array for Web Audio API playback.
 * gpt-realtime sends audio as base64-encoded PCM16.
 *
 * @param base64 - Base64-encoded PCM16 audio data
 * @returns Float32Array with values in -1.0 to 1.0 range
 */
export function pcm16ToFloat32(base64: string): Float32Array {
  // 1. Decode base64 to bytes
  const binaryString = atob(base64)
  const bytes = new Uint8Array(binaryString.length)
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }

  // 2. Create Int16Array view (PCM16 = 2 bytes per sample, little-endian)
  const int16 = new Int16Array(bytes.buffer)

  // 3. Convert to Float32 (-1.0 to 1.0 range)
  // PCM16 range: -32768 to 32767
  const float32 = new Float32Array(int16.length)
  for (let i = 0; i < int16.length; i++) {
    // Normalize: divide by 32768 to get -1.0 to ~1.0 range
    float32[i] = int16[i] / 32768
  }

  return float32
}

/**
 * Convert Float32Array audio (from mic) to base64-encoded PCM16.
 * Browser MediaRecorder gives Float32 (-1.0 to 1.0), gpt-realtime needs PCM16.
 *
 * @param float32 - Float32Array with values in -1.0 to 1.0 range
 * @returns Base64-encoded PCM16 audio data
 */
export function float32ToPcm16Base64(float32: Float32Array): string {
  // 1. Convert Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
  const int16 = new Int16Array(float32.length)
  for (let i = 0; i < float32.length; i++) {
    // Clamp to prevent overflow
    const clamped = Math.max(-1, Math.min(1, float32[i]))
    // Scale to Int16 range (multiply by 32767 for positive, 32768 for negative)
    int16[i] = clamped < 0 ? clamped * 32768 : clamped * 32767
  }

  // 2. Create Uint8Array of bytes (Int16Array is already little-endian on most platforms)
  const bytes = new Uint8Array(int16.buffer)

  // 3. Encode to base64
  let binaryString = ''
  for (let i = 0; i < bytes.length; i++) {
    binaryString += String.fromCharCode(bytes[i])
  }

  return btoa(binaryString)
}
