using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class Lanceur {
    [STAThread]
    private static void Main() {
        try {
            string folder = AppDomain.CurrentDomain.BaseDirectory;
            string config = Path.Combine(folder, "python-local.txt");
            string python = File.Exists(config) ? File.ReadAllText(config).Trim() : "";
            if (!File.Exists(python)) {
                MessageBox.Show("Python local introuvable. Indiquez le chemin de pythonw.exe dans python-local.txt. Aucun téléchargement automatique.", "Sanzo Wada", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            string script = Path.Combine(folder, "demarrer.pyw");
            if (!File.Exists(script)) throw new FileNotFoundException("demarrer.pyw manque. Conservez le dossier Application complet.");
            ProcessStartInfo start = new ProcessStartInfo(python, "-B \"" + script + "\"");
            start.WorkingDirectory = folder;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            Process.Start(start);
        } catch (Exception error) {
            MessageBox.Show(error.Message, "Sanzo Wada : démarrage impossible", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
