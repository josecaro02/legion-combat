/**
 * Cloudinary Upload Utility
 *
 * Handles image compression and upload to Cloudinary
 * Uses unsigned uploads with upload_preset (no API secret required)
 *
 * Configuration:
 * - Cloud name and upload preset should be set in environment variables
 * - Images are uploaded to the 'students/' folder
 *
 * Edge Case Note:
 * If upload to Cloudinary succeeds but backend request fails,
 * the image remains in Cloudinary without database reference.
 * This is accepted - no cleanup is performed.
 */

// Cloudinary configuration
const CLOUD_NAME = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME;
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET;
const UPLOAD_URL = `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`;

/**
 * Validate Cloudinary configuration
 * @throws {Error} If configuration is missing
 */
function validateConfig() {
  if (!CLOUD_NAME) {
    throw new Error('Cloudinary cloud name is not configured. Set VITE_CLOUDINARY_CLOUD_NAME in .env');
  }
  if (!UPLOAD_PRESET) {
    throw new Error('Cloudinary upload preset is not configured. Set VITE_CLOUDINARY_UPLOAD_PRESET in .env');
  }
}

/**
 * Compress image before upload
 * - Resizes if dimensions exceed max
 * - Converts to JPEG
 * - Compresses to meet size target
 *
 * @param {File} file - Original image file
 * @param {Object} options - Compression options
 * @param {number} [options.maxWidth=1280] - Max width
 * @param {number} [options.maxHeight=1280] - Max height
 * @param {number} [options.maxSizeMB=2] - Target max file size in MB
 * @param {number} [options.quality=0.85] - JPEG quality (0-1)
 * @returns {Promise<Blob>} - Compressed image blob
 */
export async function compressImage(file, options = {}) {
  const {
    maxWidth = 1280,
    maxHeight = 1280,
    maxSizeMB = 2,
    quality = 0.85
  } = options;

  return new Promise((resolve, reject) => {
    const img = new Image();
    const reader = new FileReader();

    reader.onload = (e) => {
      img.src = e.target.result;
    };

    reader.onerror = () => reject(new Error('Error reading file'));

    img.onload = () => {
      // Calculate new dimensions maintaining aspect ratio
      let { width, height } = img;

      if (width > maxWidth || height > maxHeight) {
        const ratio = Math.min(maxWidth / width, maxHeight / height);
        width *= ratio;
        height *= ratio;
      }

      // Create canvas for compression
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);

      // Convert to blob with compression
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Canvas to Blob conversion failed'));
            return;
          }

          // Check if compression achieved target size
          const sizeInMB = blob.size / (1024 * 1024);

          if (sizeInMB > maxSizeMB && quality > 0.3) {
            // If still too large, try with lower quality
            const newQuality = Math.max(0.3, quality - 0.2);
            canvas.toBlob(
              (newBlob) => {
                if (newBlob) {
                  resolve(newBlob);
                } else {
                  reject(new Error('Compression failed'));
                }
              },
              'image/jpeg',
              newQuality
            );
          } else {
            resolve(blob);
          }
        },
        'image/jpeg',
        quality
      );
    };

    img.onerror = () => reject(new Error('Error loading image'));

    reader.readAsDataURL(file);
  });
}

/**
 * Upload image to Cloudinary
 *
 * @param {File|Blob} file - Image file or blob to upload
 * @param {Object} options - Upload options
 * @param {string} [options.folder='students'] - Cloudinary folder
 * @returns {Promise<Object>} - Upload result with secure_url and public_id
 * @throws {Error} - If upload fails
 */
export async function uploadToCloudinary(file, options = {}) {
  validateConfig();

  const { folder = 'students' } = options;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('upload_preset', UPLOAD_PRESET);
  formData.append('folder', folder);

  // Optional: Add timestamp to prevent caching issues
  formData.append('timestamp', Date.now().toString());

  try {
    const response = await fetch(UPLOAD_URL, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || `Upload failed: ${response.status}`);
    }

    const data = await response.json();

    if (!data.secure_url) {
      throw new Error('Invalid response from Cloudinary');
    }

    return {
      secure_url: data.secure_url,
      public_id: data.public_id,
      width: data.width,
      height: data.height,
      format: data.format,
      size: data.bytes,
      folder: data.folder,
    };
  } catch (error) {
    console.error('Cloudinary upload error:', error);
    throw new Error(error.message || 'Error uploading image to Cloudinary');
  }
}

/**
 * Complete upload flow: compress and upload to Cloudinary
 *
 * @param {File} file - Original image file
 * @param {Object} options - Options for compression and upload
 * @returns {Promise<Object>} - Upload result with secure_url
 * @throws {Error} - If compression or upload fails
 */
export async function uploadStudentPhoto(file, options = {}) {
  // Step 1: Compress image
  const compressedBlob = await compressImage(file, {
    maxWidth: 1280,
    maxHeight: 1280,
    maxSizeMB: 2,
    quality: 0.85,
    ...options.compression
  });

  // Step 2: Upload to Cloudinary
  const result = await uploadToCloudinary(compressedBlob, {
    folder: 'students',
    ...options.upload
  });

  return result;
}

/**
 * Check if Cloudinary is configured
 * @returns {boolean}
 */
export function isCloudinaryConfigured() {
  return !!(CLOUD_NAME && UPLOAD_PRESET);
}

/**
 * Get Cloudinary configuration status
 * @returns {Object}
 */
export function getCloudinaryStatus() {
  return {
    configured: isCloudinaryConfigured(),
    cloudName: CLOUD_NAME ? '***' : 'not set',
    uploadPreset: UPLOAD_PRESET ? '***' : 'not set',
  };
}

export default {
  compressImage,
  uploadToCloudinary,
  uploadStudentPhoto,
  isCloudinaryConfigured,
  getCloudinaryStatus,
};
