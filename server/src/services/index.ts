const products = [
  {
    id: "T14_Gen3",
    name: "Lenovo ThinkPad T14 Gen 3",
    category: "Business Laptop",
    description:
      "A powerful and secure 14-inch business laptop, ideal for professionals needing performance and reliability.",
    specifications: {
      processor: "Intel Core i7-1260P",
      ram: "16GB DDR4",
      storage: "512GB NVMe SSD",
      display: "14-inch FHD (1920x1080) IPS",
      graphics: "Intel Iris Xe Graphics",
      os: "Windows 11 Pro",
    },
    price_usd: 1499.99,
    in_stock: true,
    image_url: "https://example.com/thinkpad_t14_gen3.jpg",
  },
  {
    id: "X1_Carbon_Gen10",
    name: "Lenovo ThinkPad X1 Carbon Gen 10",
    category: "Ultrabook",
    description:
      "The ultimate premium business ultrabook, known for its lightweight design, robust build, and exceptional performance.",
    specifications: {
      processor: "Intel Core i7-1280P",
      ram: "32GB LPDDR5",
      storage: "1TB NVMe SSD",
      display: "14-inch WQUXGA (3840x2400) OLED",
      graphics: "Intel Iris Xe Graphics",
      os: "Windows 11 Pro",
    },
    price_usd: 2199.99,
    in_stock: true,
    image_url: "https://example.com/thinkpad_x1_carbon_gen10.jpg",
  },
  {
    id: "P1_Gen5",
    name: "Lenovo ThinkPad P1 Gen 5",
    category: "Mobile Workstation",
    description:
      "A powerful mobile workstation designed for creators and engineers, offering high-end performance and dedicated graphics.",
    specifications: {
      processor: "Intel Core i9-12900H",
      ram: "64GB DDR5",
      storage: "2TB NVMe SSD",
      display: "16-inch QHD+ (2560x1600) IPS",
      graphics: "NVIDIA GeForce RTX 3070 Ti",
      os: "Windows 11 Pro",
    },
    price_usd: 3299.99,
    in_stock: false,
    image_url: "https://example.com/thinkpad_p1_gen5.jpg",
  },
  {
    id: "E15_Gen4",
    name: "Lenovo ThinkPad E15 Gen 4",
    category: "Budget Business Laptop",
    description:
      "An affordable and reliable 15-inch business laptop, perfect for everyday productivity.",
    specifications: {
      processor: "AMD Ryzen 5 5625U",
      ram: "8GB DDR4",
      storage: "256GB NVMe SSD",
      display: "15.6-inch FHD (1920x1080) IPS",
      graphics: "AMD Radeon Graphics",
      os: "Windows 11 Home",
    },
    price_usd: 899.99,
    in_stock: true,
    image_url: "https://example.com/thinkpad_e15_gen4.jpg",
  },
];

export const searchProducts = ({ query }: { query: string }) => {
  // TODO: find products with regex match of title, description, or specifications
  return products;
};
