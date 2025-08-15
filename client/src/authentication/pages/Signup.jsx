import { useState } from "react";
import { registerUser } from "../firebase/firebase.controllers.jsx";

const Signup = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
   
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [passwordStatus, setPasswordStatus] = useState(null);

    const validateDutEmail = (email) => {
        const dutEmailRegex = /^\d{8}@dut4life\.ac\.za$/;
        return dutEmailRegex.test(email);
    };

    const validatePassword = (password) => {
        const minLength = 6;
        const maxLength = 30;

        const hasLowercase = /[a-z]/.test(password);
        const hasUppercase = /[A-Z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecialChar = /[\^\$\*\.\[\]\{\}\(\)\?"!@#%&/\\,><':;|_~]/.test(password);

        const isLengthOk = password.length >= minLength && password.length <= maxLength;

        const isValid = hasLowercase && hasUppercase && hasNumber && hasSpecialChar && isLengthOk;

        return {
            isValid,
            isLengthOk,
            hasLowercase,
            hasUppercase,
            hasNumber,
            hasSpecialChar,
            minLength,
            maxLength
        };
    };

    const handlePasswordChange = (e) => {
        const pwd = e.target.value;
        setPassword(pwd);
        setPasswordStatus(validatePassword(pwd));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setSuccess("");

        if (!validateDutEmail(email)) {
            setError("Invalid DUT email format.");
            return;
        }

        const status = validatePassword(password);
        if (!status.isValid) {
            setError("Password does not meet requirements.");
            setPasswordStatus(status);
            return;
        }

        try {
            const user = await registerUser(email, password);

            localStorage.setItem("token", user.accessToken);
            localStorage.setItem("uid", user.uid);
            localStorage.setItem("email", user.email);

            setSuccess("Signup successful!");
            setEmail("");
            setPassword("");
            setPasswordStatus(null);
        } catch (err) {
            setError("Signup failed. Please try again.");
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-100 to-blue-300">
            <div className="bg-white shadow-lg rounded-lg p-8 w-full max-w-md">
                <h2 className="text-3xl font-bold mb-6 text-center text-blue-700">Sign Up</h2>
                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block mb-1 font-medium text-gray-700">Email:</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                            placeholder="12345678@dut4life.ac.za"
                        />
                    </div>
                    <div>
                        <label className="block mb-1 font-medium text-gray-700">Password:</label>
                        <input
                            type="password"
                            value={password}
                            onChange={handlePasswordChange}
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
                            placeholder="Enter a strong password"
                        />
                    </div>
                    {passwordStatus && !passwordStatus.isValid && (
                        <ul className="text-red-600 text-sm list-disc ml-5">
                            {!passwordStatus.hasLowercase && <li>Must contain a lowercase letter</li>}
                            {!passwordStatus.hasUppercase && <li>Must contain an uppercase letter</li>}
                            {!passwordStatus.hasNumber && <li>Must contain a number</li>}
                            {!passwordStatus.hasSpecialChar && <li>Must contain a special character</li>}
                            {!passwordStatus.isLengthOk && (
                                <li>
                                    Password must be {passwordStatus.minLength}-{passwordStatus.maxLength} characters
                                </li>
                            )}
                        </ul>
                    )}
                    <button
                        type="submit"
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded transition duration-200"
                    >
                        Sign Up
                    </button>
                </form>
                {error && <p className="mt-4 text-center text-red-600">{error}</p>}
                {success && <p className="mt-4 text-center text-green-600">{success}</p>}
                  <p>Aready have an account? <a href="/auth/login" className="text-blue-500 hover:underline">Log In</a></p>
            </div>
        </div>
    );
};

export default Signup;
