// Shows a product's photo, falling back to the category emoji tile if the
// product has no image or the image fails to load (e.g. offline). Used on
// both the product cards and the detail page.

import { useState } from "react";
import { categoryVisual } from "../categoryVisual";

function ProductImage({ product, className }) {
  const [failed, setFailed] = useState(false);
  const visual = categoryVisual(product.category);
  const showImage = product.image_url && !failed;

  return (
    <div
      className={className}
      style={
        showImage
          ? undefined
          : { background: `linear-gradient(135deg, ${visual.from}, ${visual.to})` }
      }
    >
      {showImage ? (
        <img
          src={product.image_url}
          alt={product.name}
          className="thumb-img"
          loading="lazy"
          onError={() => setFailed(true)}
        />
      ) : (
        <span>{visual.emoji}</span>
      )}
    </div>
  );
}

export default ProductImage;
