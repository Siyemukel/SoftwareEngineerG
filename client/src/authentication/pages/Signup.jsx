import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const Signup = () => {
    const [form, setForm] = useState({
        full_name: "",
        username: "",
        email: "",
        password: ""
    });
    const [message, setMessage] = useState("");
    const [errors, setErrors] = useState({});
    const navigate = useNavigate();

    const validate = async () => {
        const errs = {};

        if (!/^\d{8}@dut4life\.ac\.za$/.test(form.email)) {
            errs.email = "Email must be a valid DUT email (e.g. 22289351@dut4life.ac.za)";
        } else {
            const res = await fetch("http://127.0.0.1:5000/api/auth/check-email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: form.email })
            });
            const data = await res.json();
            if (data.exists) errs.email = "Email is already registered";
        }

        if (!form.username) {
            errs.username = "Username is required";
        } else {
            const res = await fetch("http://127.0.0.1:5000/api/auth/check-username", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username: form.username })
            });
            const data = await res.json();
            if (data.exists) errs.username = "Username is already taken";
        }

        if (!/^[A-Z][a-z]+ [A-Z][a-z]+$/.test(form.full_name)) {
            errs.full_name = "Full name must be in format: Name Surname (capitalize first letters)";
        }

        if (
            !/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/.test(form.password)
        ) {
            errs.password =
                "Password must be at least 8 characters, include upper and lower case, a number, and a special character.";
        }

        setErrors(errs);
        return Object.keys(errs).length === 0;
    };

    const handleChange = (e) => {
        setForm({ ...form, [e.target.name]: e.target.value });
        setErrors({ ...errors, [e.target.name]: undefined });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage("");
        if (!(await validate())) return;

        try {
            const response = await fetch("http://127.0.0.1:5000/api/auth/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(form)
            });
            const data = await response.json();
            if (response.ok) {
                setMessage("Signup successful! You can now log in.");

                localStorage.setItem("token", data.token);
                localStorage.setItem("uid", data.user.uid);
                localStorage.setItem("email", data.user.email);
                localStorage.setItem("username", data.user.username);

                setTimeout(() => navigate("/user/dashboard"), 1000);
            } else {
                setMessage(data.message || "Signup failed.");
            }


        } catch (err) {
            setMessage("Network error.");
        }
    };

    return (
        <>
            <h1>Signup</h1>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    name="full_name"
                    placeholder="Full Name"
                    value={form.full_name}
                    onChange={handleChange}
                    required
                />
                {errors.full_name && <p style={{ color: "red" }}>{errors.full_name}</p>}
                <input
                    type="text"
                    name="username"
                    placeholder="Username"
                    value={form.username}
                    onChange={handleChange}
                    required
                />
                {errors.username && <p style={{ color: "red" }}>{errors.username}</p>}
                <input
                    type="email"
                    name="email"
                    placeholder="Email"
                    value={form.email}
                    onChange={handleChange}
                    required
                />
                {errors.email && <p style={{ color: "red" }}>{errors.email}</p>}
                <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    value={form.password}
                    onChange={handleChange}
                    required
                />
                {errors.password && <p style={{ color: "red" }}>{errors.password}</p>}
                <button type="submit">Sign Up</button>
            </form>
            {message && <p>{message}</p>}
        </>
    );
};

export default Signup;