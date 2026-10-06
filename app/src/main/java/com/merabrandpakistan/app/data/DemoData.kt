package com.merabrandpakistan.app.data

/** Sample catalogue used until the real server is connected. All names are made up. */
object DemoData {
    const val DEMO_PIN = "1234"

    val halls = listOf(
        Hall("H1", "Hall 1", "Manufacturing & Lifestyle"),
        Hall("H2", "Hall 2", "Food & Agriculture"),
        Hall("H3", "Hall 3", "Technology & Services"),
    )

    val exhibitors = listOf(
        Exhibitor(
            "EXH001", "Lahore Looms", "Textiles", "Premium fabrics, woven in Punjab",
            "Family-owned weaving mill exporting cotton and blended fabrics to 20 countries.",
            "H1", "A-01", "sales@lahorelooms.example", "+92 300 0000001",
        ),
        Exhibitor(
            "EXH002", "Karachi Apparel Co.", "Fashion", "Ready-to-wear for global brands",
            "Private-label garment manufacturer specialising in denim and knitwear.",
            "H1", "A-07", "hello@karachiapparel.example", "+92 300 0000002",
        ),
        Exhibitor(
            "EXH003", "Sialkot Sports Gear", "Sports goods", "Match-quality gear from Sialkot",
            "Footballs, cricket equipment and fitness wear made to international standards.",
            "H1", "B-03", "info@sialkotsports.example", "+92 300 0000003",
        ),
        Exhibitor(
            "EXH004", "Multan Mango Foods", "Food", "Pakistan's finest mangoes, packed fresh",
            "Pulp, juices and dried fruit made from hand-picked Multan mangoes.",
            "H2", "C-02", "orders@multanmango.example", "+92 300 0000004",
        ),
        Exhibitor(
            "EXH005", "Peshawar Dry Fruits", "Food", "Nuts, dates and spices",
            "Wholesale supplier of dry fruits, spices and gift boxes.",
            "H2", "C-09", "sales@peshawardryfruits.example", "+92 300 0000005",
        ),
        Exhibitor(
            "EXH006", "Islamabad Digital Labs", "Software", "Apps and e-commerce for local brands",
            "Software house building mobile apps, websites and ERP tools for SMEs.",
            "H3", "D-04", "team@isbdigital.example", "+92 300 0000006",
        ),
        Exhibitor(
            "EXH007", "Faisalabad Packaging", "Packaging", "Boxes and labels that sell your brand",
            "Custom printed packaging, corrugated boxes and branded labels.",
            "H3", "D-11", "contact@fsdpackaging.example", "+92 300 0000007",
        ),
        Exhibitor(
            "EXH008", "Gwadar Logistics", "Logistics", "Door-to-door export shipping",
            "Freight forwarding, customs clearance and warehousing for exporters.",
            "H3", "E-05", "ops@gwadarlogistics.example", "+92 300 0000008",
        ),
    )

    val products = listOf(
        Product("P01", "EXH001", "Combed Cotton Poplin", "120 gsm, 58\" width, available in 40 colours."),
        Product("P02", "EXH001", "Organic Cotton Twill", "GOTS-certified twill for workwear and uniforms."),
        Product("P03", "EXH002", "Stretch Denim Jeans", "Men's and women's fits, low minimum order."),
        Product("P04", "EXH002", "Knit Hoodies", "Fleece-lined hoodies with custom embroidery."),
        Product("P05", "EXH003", "Match Football (Size 5)", "Thermo-bonded, FIFA Quality tested."),
        Product("P06", "EXH003", "Cricket Bat – English Willow", "Hand-selected willow, ready to play."),
        Product("P07", "EXH004", "Sindhri Mango Pulp", "Aseptic 3.1 kg tins, no added sugar."),
        Product("P08", "EXH004", "Dried Mango Slices", "Soft dried slices in 250 g pouches."),
        Product("P09", "EXH005", "Premium Medjool Dates", "1 kg gift box, export grade."),
        Product("P10", "EXH005", "Chilgoza Pine Nuts", "Hand-sorted, vacuum packed."),
        Product("P11", "EXH006", "Store-in-a-Box", "Ready-made online store for small brands."),
        Product("P12", "EXH006", "Inventory & Billing App", "Android and web app for shops and distributors."),
        Product("P13", "EXH007", "Printed Mailer Boxes", "Full-colour boxes, from 500 pieces."),
        Product("P14", "EXH007", "Woven Brand Labels", "Satin and damask labels for garments."),
        Product("P15", "EXH008", "Sea Freight – FCL/LCL", "Weekly sailings from Karachi and Port Qasim."),
        Product("P16", "EXH008", "Customs Clearance", "Documentation and clearance support."),
    )

    val meetingSlots = listOf(
        "Day 1 · 10:00 AM",
        "Day 1 · 12:00 PM",
        "Day 1 · 03:00 PM",
        "Day 2 · 10:00 AM",
        "Day 2 · 12:00 PM",
        "Day 2 · 03:00 PM",
    )

    /** Exhibitor login IDs and PINs. Every demo exhibitor uses [DEMO_PIN]. */
    val exhibitorPins: Map<String, String> = exhibitors.associate { it.id to DEMO_PIN }
}
