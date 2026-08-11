import express from "express";
import mysql from "mysql2/promise";
import path, { dirname } from "path";
import { fileURLToPath } from "url";
import cookieParser from "cookie-parser";
import bcrypt from "bcrypt";

// ✅ Fix for __dirname in ES modules (must be before using __dirname)
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 4000;

// View Engine Setup
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, "public")));

// MySQL Configuration (using pool)
const pool = await mysql.createPool({
  host: "localhost",
  user: "root",
  password: "Viraj@1000",
  database: "investment",
});

console.log("Database connected!");

// Routes
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "/public/index.html"));
});

app.get("/login", (req, res) => {
  res.sendFile(path.join(__dirname, "/public/login.html"));
});

app.get("/signup", (req, res) => {
  res.sendFile(path.join(__dirname, "/public/signup.html"));
});

let h = ""; // email holder

// Login route
app.post("/login", async (req, res) => {
  const { email, password } = req.body;
  h = email;

  try {
    const [rows] = await pool.query("SELECT * FROM test WHERE email = ?", [email]);

    if (rows.length > 0) {
      const isMatch = await bcrypt.compare(password, rows[0].password);
      if (isMatch) {
        res.sendFile(path.join(__dirname, "/public/dashboard.html"));
      } else {
        res.status(401).sendFile(path.join(__dirname, "/public/signup.html"));
      }
    } else {
      res.status(401).sendFile(path.join(__dirname, "/public/signup.html"));
    }
  } catch (err) {
    console.error("Error checking login credentials:", err.stack);
    res.status(500).send("An error occurred. Please try again.");
  }
});

// Signup route
app.post("/signup", async (req, res) => {
  const { email, password } = req.body;
  h = email;

  try {
    const [existing] = await pool.query("SELECT * FROM test WHERE email = ?", [email]);
    if (existing.length > 0) {
      return res.status(409).send("Email already registered.");
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    await pool.query("INSERT INTO test (email, password) VALUES (?, ?)", [email, hashedPassword]);

    res.cookie("email", email);
    res.sendFile(path.join(__dirname, "/public/information.html"));
  } catch (err) {
    console.error("Error inserting data:", err.stack);
    res.status(500).sendFile(path.join(__dirname, "/public/signup.html"));
  }
});

// Submit additional user info
app.post("/submit-info", async (req, res) => {
  console.log(req.body);

  const email = h;

  const {
    fullname,
    age,
    gender,
    education_level,
    annual_income,
    investment_amount,
    financial_knowledge,
    risk_tolerance,
    investment_horizon
  } = req.body;

  const query = `
    UPDATE test
    SET 
      fullname = ?,
      age = ?, 
      gender = ?, 
      education_level = ?, 
      annual_income = ?, 
      investment_amount = ?, 
      financial_knowledge = ?, 
      risk_tolerance = ?, 
      investment_horizon = ?
    WHERE email = ?
  `;

  const values = [
    fullname,
    age,
    gender,
    education_level,
    annual_income,
    investment_amount,
    financial_knowledge,
    risk_tolerance,
    investment_horizon,
    email
  ];

  try {
    await pool.execute(query, values);
    res.sendFile(path.join(__dirname, "/public/login.html"));
  } catch (err) {
    console.error("Error updating data:", err.stack);
    res.sendFile(path.join(__dirname, "/public/signup.html"));
  }
});


app.get("/profile", async (req, res) => {
    const email = h; // ?email=user@example.com
    try {
      const [rows] = await pool.execute("SELECT * FROM test WHERE email = ?", [email]);
  
      if (rows.length === 0) {
        return res.send("User not found");
      }
  
      const user = rows[0];
  
      res.render("profile", {
        fullname: user.fullname,
        email: user.email,
        age: user.age,
        gender: user.gender,
        education_level: user.education_level,
        annual_income: user.annual_income,
        investment_amount: user.investment_amount,
        financial_knowledge: user.financial_knowledge,
        risk_tolerance: user.risk_tolerance,
        investment_horizon: user.investment_horizon
      });
    } catch (error) {
      console.error("Error fetching profile:", error);
      res.status(500).send("Internal Server Error");
    }
  });


  app.get("/update-info", (req, res) => {
    res.redirect("/information.html");
  });



  app.get("/dashboard", async (req, res) => {
    try {
      const [rows] = await pool.query("SELECT * FROM test WHERE email = ?", [h]);
  
      if (rows.length === 0) return res.send("User not found");
  
      const user = rows[0];
  
      // ✅ Extract only the fields needed for Flask
      const flaskInput = {
        age: user.age,
        gender: user.gender,
        education_level: user.education_level,
        annual_income: user.annual_income,
        investment_amount: user.investment_amount,
        financial_knowledge: user.financial_knowledge,
        risk_tolerance: user.risk_tolerance,
        investment_horizon: user.investment_horizon
      };
  
      console.log("User data being sent to Flask:", flaskInput);
  
      // ✅ Send trimmed data to Flask
      const fetch = (await import("node-fetch")).default;
      const response = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(flaskInput)
      });
  
      const prediction = await response.json();
      console.log("✅ AI Response:", prediction);
  
      res.render("dashboard", {
        fullname: user.fullname,
        stocks: prediction.stocks,
        bonds: prediction.bonds,
        gold: prediction.gold,
        real_estate: prediction.real_estate,
        chart: prediction.chart
      });
    } catch (err) {
      console.error("Prediction error:", err);
      res.status(500).send("Server error");
    }
  });


  
  
  

// Start server
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
