"""Image face preparation and alignment for lip-sync."""

import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class FacePreparator:
    """Prepares face images for lip-sync processing."""
    
    def __init__(self, target_size: int = 512):
        self.target_size = target_size
        self.face_cascade = None
        self.profile_cascade = None
        self._load_cascades()
    
    def _load_cascades(self):
        """Load OpenCV face cascade classifiers."""
        try:
            # Load frontal face cascade
            frontal_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(frontal_path)
            
            # Load profile face cascade for better detection
            profile_path = cv2.data.haarcascades + 'haarcascade_profileface.xml'
            self.profile_cascade = cv2.CascadeClassifier(profile_path)
            
            if self.face_cascade.empty():
                logger.warning("Failed to load frontal face cascade classifier")
                self.face_cascade = None
            else:
                logger.info("Frontal face cascade classifier loaded successfully")
                
            if self.profile_cascade.empty():
                logger.warning("Failed to load profile face cascade classifier")
                self.profile_cascade = None
            else:
                logger.info("Profile face cascade classifier loaded successfully")
                
        except Exception as e:
            logger.warning(f"Could not load face cascades: {e}")
            self.face_cascade = None
            self.profile_cascade = None
    
    def prepare_face(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Prepare face image for lip-sync processing."""
        try:
            # Load image
            image = cv2.imread(str(input_path))
            if image is None:
                raise ValueError(f"Could not load image: {input_path}")
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect face
            face_info = self._detect_face(image_rgb)
            
            if face_info:
                # Crop and align face
                cropped_face = self._crop_face(image_rgb, face_info)
                aligned_face = self._align_face(cropped_face)
            else:
                # No face detected, use center crop
                logger.warning("No face detected, using center crop")
                aligned_face = self._center_crop(image_rgb)
            
            # Resize to target size
            resized_face = self._resize_face(aligned_face)
            
            # Save prepared face
            self._save_face(resized_face, output_path)
            
            return {
                "success": True,
                "face_detected": face_info is not None,
                "face_info": face_info,
                "output_size": (self.target_size, self.target_size),
                "original_size": image_rgb.shape[:2]
            }
            
        except Exception as e:
            logger.error(f"Face preparation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "face_detected": False
            }
    
    def _detect_face(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect face in image using multiple methods for robustness."""
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Try multiple detection methods
            all_faces = []
            
            # Method 1: Frontal face detection with multiple scales
            if self.face_cascade is not None:
                faces_frontal = self._detect_faces_with_multiple_scales(
                    gray, self.face_cascade, "frontal"
                )
                all_faces.extend(faces_frontal)
            
            # Method 2: Profile face detection
            if self.profile_cascade is not None:
                faces_profile = self._detect_faces_with_multiple_scales(
                    gray, self.profile_cascade, "profile"
                )
                all_faces.extend(faces_profile)
            
            # Method 3: Template matching for cartoon/anime faces
            faces_template = self._detect_cartoon_faces(gray, image)
            all_faces.extend(faces_template)
            
            # Method 4: Edge-based detection for stylized faces
            faces_edge = self._detect_edge_based_faces(gray, image)
            all_faces.extend(faces_edge)
            
            if len(all_faces) == 0:
                logger.warning("No faces detected with any method, using center crop fallback")
                # Fallback: create a center crop as if a face was detected
                h, w = image.shape[:2]
                size = min(h, w)
                x = (w - size) // 2
                y = (h - size) // 2
                return {
                    "x": int(x),
                    "y": int(y),
                    "width": int(size),
                    "height": int(size),
                    "center_x": int(x + size // 2),
                    "center_y": int(y + size // 2),
                    "confidence": 0.1,  # Low confidence for fallback
                    "method": "center_crop_fallback"
                }
            
            # Remove duplicate faces and select the best one
            best_face = self._select_best_face(all_faces, image.shape)
            
            if best_face is None:
                logger.warning("No valid face found after filtering duplicates")
                return None
            
            logger.info(f"Face detected using method: {best_face.get('method', 'unknown')} with confidence: {best_face.get('confidence', 0):.2f}")
            
            # Add padding around the face
            x, y, w, h = best_face["x"], best_face["y"], best_face["width"], best_face["height"]
            padding = int(min(w, h) * 0.3)  # Increased padding for better cropping
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(image.shape[1] - x, w + 2 * padding)
            h = min(image.shape[0] - y, h + 2 * padding)
            
            return {
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "center_x": int(x + w // 2),
                "center_y": int(y + h // 2),
                "confidence": float(best_face.get("confidence", 0.5)),
                "method": str(best_face.get("method", "unknown"))
            }
            
        except Exception as e:
            logger.warning(f"Face detection failed: {e}")
            return None
    
    def _detect_faces_with_multiple_scales(self, gray: np.ndarray, cascade, method_name: str) -> List[Dict[str, Any]]:
        """Detect faces using multiple scale factors for better coverage."""
        faces = []
        
        # Try different scale factors and min neighbors
        scale_factors = [1.05, 1.1, 1.2, 1.3]
        min_neighbors_list = [3, 5, 7]
        min_sizes = [(20, 20), (30, 30), (40, 40)]
        
        for scale_factor in scale_factors:
            for min_neighbors in min_neighbors_list:
                for min_size in min_sizes:
                    try:
                        detected = cascade.detectMultiScale(
                            gray,
                            scaleFactor=scale_factor,
                            minNeighbors=min_neighbors,
                            minSize=min_size,
                            flags=cv2.CASCADE_SCALE_IMAGE
                        )
                        
                        for (x, y, w, h) in detected:
                            # Calculate confidence based on size and position
                            confidence = min(1.0, (w * h) / (gray.shape[0] * gray.shape[1] * 0.1))
                            
                            faces.append({
                                "x": int(x),
                                "y": int(y),
                                "width": int(w),
                                "height": int(h),
                                "confidence": confidence,
                                "method": method_name
                            })
                    except Exception as e:
                        logger.debug(f"Detection failed for {method_name}: {e}")
                        continue
        
        return faces
    
    def _detect_cartoon_faces(self, gray: np.ndarray, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect cartoon/anime faces using template matching and color analysis."""
        faces = []
        
        try:
            # Look for circular/oval regions that could be faces
            # Use HoughCircles to find circular regions
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=30,
                param1=50,
                param2=30,
                minRadius=20,
                maxRadius=min(gray.shape) // 2
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    # Convert circle to rectangle
                    w = h = int(r * 1.4)  # Make it slightly rectangular
                    x = max(0, x - w // 2)
                    y = max(0, y - h // 2)
                    w = min(image.shape[1] - x, w)
                    h = min(image.shape[0] - y, h)
                    
                    # Check if this region has face-like characteristics
                    if self._is_face_like_region(image[y:y+h, x:x+w]):
                        confidence = 0.6  # Medium confidence for cartoon detection
                        faces.append({
                            "x": x,
                            "y": y,
                            "width": w,
                            "height": h,
                            "confidence": confidence,
                            "method": "cartoon_circle"
                        })
            
            # Also try detecting based on skin tone regions
            skin_faces = self._detect_skin_tone_faces(image)
            faces.extend(skin_faces)
            
        except Exception as e:
            logger.debug(f"Cartoon face detection failed: {e}")
        
        return faces
    
    def _detect_edge_based_faces(self, gray: np.ndarray, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces using edge detection for stylized images."""
        faces = []
        
        try:
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by aspect ratio and size
                aspect_ratio = w / h
                area = w * h
                total_area = gray.shape[0] * gray.shape[1]
                
                if (0.7 <= aspect_ratio <= 1.4 and  # Face-like aspect ratio
                    area > total_area * 0.01 and    # Not too small
                    area < total_area * 0.5):       # Not too large
                    
                    # Check if this region looks like a face
                    if self._is_face_like_region(image[y:y+h, x:x+w]):
                        confidence = 0.4  # Lower confidence for edge-based detection
                        faces.append({
                            "x": x,
                            "y": y,
                            "width": w,
                            "height": h,
                            "confidence": confidence,
                            "method": "edge_based"
                        })
        
        except Exception as e:
            logger.debug(f"Edge-based face detection failed: {e}")
        
        return faces
    
    def _detect_skin_tone_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces based on skin tone regions."""
        faces = []
        
        try:
            # Convert to HSV for better skin detection
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Define skin tone range
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            
            # Create mask for skin regions
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # Apply morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours of skin regions
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size and aspect ratio
                aspect_ratio = w / h
                area = w * h
                total_area = image.shape[0] * image.shape[1]
                
                if (0.6 <= aspect_ratio <= 1.6 and  # Face-like aspect ratio
                    area > total_area * 0.005 and   # Not too small
                    area < total_area * 0.3):       # Not too large
                    
                    confidence = 0.5  # Medium confidence for skin tone detection
                    faces.append({
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "confidence": confidence,
                        "method": "skin_tone"
                    })
        
        except Exception as e:
            logger.debug(f"Skin tone face detection failed: {e}")
        
        return faces
    
    def _is_face_like_region(self, region: np.ndarray) -> bool:
        """Check if a region has face-like characteristics."""
        if region.size == 0:
            return False
        
        try:
            # Check if region has reasonable size
            h, w = region.shape[:2]
            if h < 20 or w < 20:
                return False
            
            # Check for symmetry (faces are generally symmetric)
            if w > h:
                left_half = region[:, :w//2]
                right_half = region[:, w//2:]
                right_half_flipped = cv2.flip(right_half, 1)
                
                # Resize to same dimensions for comparison
                if left_half.shape != right_half_flipped.shape:
                    min_w = min(left_half.shape[1], right_half_flipped.shape[1])
                    left_half = left_half[:, :min_w]
                    right_half_flipped = right_half_flipped[:, :min_w]
                
                # Calculate similarity
                if left_half.size > 0 and right_half_flipped.size > 0:
                    similarity = cv2.matchTemplate(left_half, right_half_flipped, cv2.TM_CCOEFF_NORMED)[0][0]
                    if similarity > 0.3:  # Some level of symmetry
                        return True
            
            # Check for color distribution (faces usually have varied colors)
            if len(region.shape) == 3:
                std_dev = np.std(region)
                if std_dev > 20:  # Sufficient color variation
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Face-like region check failed: {e}")
            return False
    
    def _select_best_face(self, faces: List[Dict[str, Any]], image_shape: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        """Select the best face from multiple detections."""
        if not faces:
            return None
        
        # Remove duplicate faces (overlapping regions)
        unique_faces = self._remove_duplicate_faces(faces)
        
        if not unique_faces:
            return None
        
        # Score faces based on multiple criteria
        best_face = None
        best_score = -1
        
        for face in unique_faces:
            score = self._score_face(face, image_shape)
            if score > best_score:
                best_score = score
                best_face = face
        
        return best_face
    
    def _remove_duplicate_faces(self, faces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate/overlapping face detections."""
        if len(faces) <= 1:
            return faces
        
        # Sort by confidence
        faces.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        unique_faces = []
        for face in faces:
            is_duplicate = False
            for unique_face in unique_faces:
                if self._faces_overlap(face, unique_face):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_faces.append(face)
        
        return unique_faces
    
    def _faces_overlap(self, face1: Dict[str, Any], face2: Dict[str, Any], threshold: float = 0.3) -> bool:
        """Check if two face detections overlap significantly."""
        x1, y1, w1, h1 = face1["x"], face1["y"], face1["width"], face1["height"]
        x2, y2, w2, h2 = face2["x"], face2["y"], face2["width"], face2["height"]
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return False
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - intersection_area
        
        overlap_ratio = intersection_area / union_area if union_area > 0 else 0
        return overlap_ratio > threshold
    
    def _score_face(self, face: Dict[str, Any], image_shape: Tuple[int, int]) -> float:
        """Score a face detection based on multiple criteria."""
        x, y, w, h = face["x"], face["y"], face["width"], face["height"]
        img_h, img_w = image_shape[:2]
        
        # Base score from confidence
        score = face.get("confidence", 0.5)
        
        # Size score (prefer faces that are not too small or too large)
        face_area = w * h
        total_area = img_w * img_h
        size_ratio = face_area / total_area
        
        if 0.01 <= size_ratio <= 0.3:  # Good size range
            score += 0.2
        elif size_ratio < 0.01:  # Too small
            score -= 0.3
        else:  # Too large
            score -= 0.1
        
        # Position score (prefer faces closer to center)
        center_x = x + w // 2
        center_y = y + h // 2
        img_center_x = img_w // 2
        img_center_y = img_h // 2
        
        distance_from_center = np.sqrt((center_x - img_center_x)**2 + (center_y - img_center_y)**2)
        max_distance = np.sqrt(img_w**2 + img_h**2) / 2
        position_score = 1 - (distance_from_center / max_distance)
        score += position_score * 0.2
        
        # Aspect ratio score (prefer face-like aspect ratios)
        aspect_ratio = w / h
        if 0.7 <= aspect_ratio <= 1.4:  # Good face aspect ratio
            score += 0.1
        
        return score
    
    def _crop_face(self, image: np.ndarray, face_info: Dict[str, Any]) -> np.ndarray:
        """Crop face region from image."""
        x = face_info["x"]
        y = face_info["y"]
        w = face_info["width"]
        h = face_info["height"]
        
        return image[y:y+h, x:x+w]
    
    def _align_face(self, face_image: np.ndarray) -> np.ndarray:
        """Align face to be centered and square."""
        h, w = face_image.shape[:2]
        
        # Make it square by taking the larger dimension
        size = max(h, w)
        
        # Create square canvas
        square_image = np.zeros((size, size, 3), dtype=np.uint8)
        
        # Center the face in the square
        start_y = (size - h) // 2
        start_x = (size - w) // 2
        square_image[start_y:start_y+h, start_x:start_x+w] = face_image
        
        return square_image
    
    def _center_crop(self, image: np.ndarray) -> np.ndarray:
        """Center crop image to square."""
        h, w = image.shape[:2]
        size = min(h, w)
        
        start_y = (h - size) // 2
        start_x = (w - size) // 2
        
        return image[start_y:start_y+size, start_x:start_x+size]
    
    def _resize_face(self, face_image: np.ndarray) -> np.ndarray:
        """Resize face to target size."""
        return cv2.resize(face_image, (self.target_size, self.target_size))
    
    def _save_face(self, face_image: np.ndarray, output_path: Path) -> None:
        """Save prepared face image."""
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert back to PIL Image for saving
        pil_image = Image.fromarray(face_image)
        pil_image.save(output_path, "PNG")
        
        logger.info(f"Prepared face saved to: {output_path}")


def prepare_face_image(input_path: Path, output_path: Path, target_size: int = 512) -> Dict[str, Any]:
    """Prepare a face image for lip-sync processing."""
    preparator = FacePreparator(target_size=target_size)
    return preparator.prepare_face(input_path, output_path)


def create_sample_face(output_path: Path, size: int = 512) -> None:
    """Create a sample face image for testing."""
    # Create a simple face-like image
    image = Image.new('RGB', (size, size), color='lightblue')
    draw = ImageDraw.Draw(image)
    
    # Face outline
    margin = size // 8
    face_rect = [margin, margin, size - margin, size - margin]
    draw.ellipse(face_rect, fill='peachpuff', outline='black', width=2)
    
    # Eyes
    eye_size = size // 16
    left_eye = [size // 3, size // 3, size // 3 + eye_size, size // 3 + eye_size]
    right_eye = [2 * size // 3 - eye_size, size // 3, 2 * size // 3, size // 3 + eye_size]
    draw.ellipse(left_eye, fill='white', outline='black', width=1)
    draw.ellipse(right_eye, fill='white', outline='black', width=1)
    
    # Eye pupils
    pupil_size = eye_size // 3
    left_pupil = [left_eye[0] + eye_size // 3, left_eye[1] + eye_size // 3, 
                  left_eye[0] + eye_size // 3 + pupil_size, left_eye[1] + eye_size // 3 + pupil_size]
    right_pupil = [right_eye[0] + eye_size // 3, right_eye[1] + eye_size // 3,
                   right_eye[0] + eye_size // 3 + pupil_size, right_eye[1] + eye_size // 3 + pupil_size]
    draw.ellipse(left_pupil, fill='black')
    draw.ellipse(right_pupil, fill='black')
    
    # Nose
    nose_points = [(size // 2, size // 2), (size // 2 - size // 20, size // 2 + size // 20), 
                   (size // 2 + size // 20, size // 2 + size // 20)]
    draw.polygon(nose_points, fill='peachpuff', outline='black', width=1)
    
    # Mouth
    mouth_rect = [size // 3, 2 * size // 3, 2 * size // 3, 2 * size // 3 + size // 20]
    draw.arc(mouth_rect, 0, 180, fill='red', width=3)
    
    # Save image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")
    logger.info(f"Sample face created: {output_path}")
